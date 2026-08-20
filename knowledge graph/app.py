"""FastAPI orchestration server for the local GraphRAG pipeline.

Run with:  uvicorn app:app --reload
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ollama
import psycopg2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# These imports intentionally reuse the project's established document reader,
# embedding model and Ollama/Qwen fact-extraction prompt.
from INGESTION.chunking import chunk_document
from EXTRACTION.embedding import create_embeddings
from EXTRACTION import facts
from ONTOLOGY import ontology

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UI_FILE = PROJECT_ROOT / "UI" / "index.html"
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}
COLLECTION_NAME = "documents"
QDRANT_URL = "http://localhost:6333"
OLLAMA_MODEL = facts.OLLAMA_MODEL

app = FastAPI(title="Local GraphRAG", version="1.0.0")
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()
ollama_lock = threading.Lock()  # A local model normally processes one request at a time.

# Every Ollama call in the app (fact extraction in facts.py, and the
# query call below) is serialized behind ollama_lock. Without a
# timeout, one stuck call holds that lock forever and freezes fact
# extraction AND querying for every other job on the server too — that
# is what "the pipeline just stopped" looks like from the outside.
OLLAMA_TIMEOUT = 120
ollama_client = ollama.Client(timeout=OLLAMA_TIMEOUT)

STAGES = ["upload", "chunking", "vector_store", "fact_extraction", "ontology", "graph"]


@app.on_event("startup")
async def open_local_ui() -> None:
    """Open the upload page for the normal local-development run.

    Set OPEN_BROWSER=0 when running this server on another machine or in a
    container.
    """
    if os.getenv("OPEN_BROWSER", "1") == "1":
        webbrowser.open_new_tab("http://127.0.0.1:8000/")


class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_job(filename: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()), "filename": filename, "state": "queued",
        "created_at": now(), "updated_at": now(), "error": None,
        "stages": {stage: {"state": "pending", "detail": "", "progress": 0} for stage in STAGES},
    }


def update_stage(job_id: str, stage: str, state: str, detail: str = "", progress: int | None = None) -> None:
    with jobs_lock:
        job = jobs[job_id]
        item = job["stages"][stage]
        item.update({"state": state, "detail": detail})
        if progress is not None:
            item["progress"] = progress
        job["updated_at"] = now()


def public_job(job_id: str) -> dict[str, Any]:
    with jobs_lock:
        if job_id not in jobs:
            raise KeyError(job_id)
        return {**jobs[job_id], "stages": {k: dict(v) for k, v in jobs[job_id]["stages"].items()}}


def qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    names = {item.name for item in client.get_collections().collections}
    if COLLECTION_NAME not in names:
        client.create_collection(COLLECTION_NAME, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))


def store_document_vectors(job_id: str, chunks: list[str]) -> list[str]:
    client = qdrant_client()

    def report_batch(done: int, total: int) -> None:
        # Embedding a whole document is one call that can take minutes;
        # without this the stage sits frozen at its starting percentage
        # the entire time, which looks identical to a hang.
        update_stage(job_id, "vector_store", "running", f"Embedded batch {done} of {total}", int(done * 90 / total))

    vectors = create_embeddings(chunks, on_batch_done=report_batch)
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count.")
    ensure_collection(client, len(vectors[0]))
    ids = [str(uuid.uuid4()) for _ in chunks]
    points = [
        PointStruct(id=point_id, vector=vector.tolist(), payload={
            "source_chunk_id": point_id, "document_id": job_id,
            "filename": jobs[job_id]["filename"], "chunk_number": index, "text": chunk,
        })
        for index, (point_id, chunk, vector) in enumerate(zip(ids, chunks, vectors), start=1)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    return ids


def extract_document_facts(job_id: str, chunk_ids: list[str], chunks: list[str]) -> int:
    facts.create_fact_table()
    conn = facts.get_connection()
    cursor = conn.cursor()
    count = 0
    try:
        for index, (chunk_id, text) in enumerate(zip(chunk_ids, chunks), start=1):
            try:
                # Keep the existing local-Qwen extraction prompt and Pydantic validation.
                with ollama_lock:
                    result = facts.extract_facts_from_chunk(text)
                for fact in result.facts:
                    facts.insert_fact(cursor, chunk_id, fact)
                    count += 1
                conn.commit()  # Facts survive if a later chunk fails.
                update_stage(job_id, "fact_extraction", "running", f"Processed chunk {index} of {len(chunks)}", int(index * 100 / len(chunks)))
            except Exception as exc:
                conn.rollback()
                update_stage(job_id, "fact_extraction", "running", f"Chunk {index} failed: {exc}; continuing", int(index * 100 / len(chunks)))
    finally:
        cursor.close()
        conn.close()
    return count


def derive_ontology_for_document(chunk_ids: list[str]) -> tuple[int, int]:
    """Build a lightweight ontology from observed facts; no OpenAI normalizer."""
    ontology.create_tables()
    conn = facts.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT subject_type FROM extracted_facts WHERE source_chunk_id = ANY(%s)
            UNION SELECT DISTINCT object_type FROM extracted_facts WHERE source_chunk_id = ANY(%s)
        """, (chunk_ids, chunk_ids))
        node_types = [row[0] for row in cursor.fetchall() if row[0]]
        for name in node_types:
            cursor.execute("""INSERT INTO ontology_nodes (name, description) VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING""", (name, "Entity type observed in uploaded documents."))
        cursor.execute("""
            SELECT DISTINCT relationship, subject_type, object_type FROM extracted_facts
            WHERE source_chunk_id = ANY(%s)
        """, (chunk_ids,))
        relationships = cursor.fetchall()
        for name, source, target in relationships:
            cursor.execute("""INSERT INTO ontology_relationships (name, source_node, target_node, description)
                VALUES (%s, %s, %s, %s) ON CONFLICT (name, source_node, target_node) DO NOTHING""",
                (name, source, target, "Relationship observed in uploaded documents."))
        conn.commit()
        return len(node_types), len(relationships)
    finally:
        cursor.close()
        conn.close()


def build_graph_if_available() -> str:
    """Use the project's graph builder, but keep Neo4j optional for answering."""
    graph_dir = str(PROJECT_ROOT / "graphs")
    if graph_dir not in sys.path:
        sys.path.insert(0, graph_dir)
    import build_graph
    try:
        build_graph.build_graph()
    finally:
        build_graph.driver.close()
    return "Neo4j graph updated."


def run_pipeline_sync(job_id: str, path: Path) -> None:
    try:
        with jobs_lock:
            jobs[job_id]["state"] = "running"
        update_stage(job_id, "upload", "completed", "File saved", 100)
        update_stage(job_id, "chunking", "running", "Reading document", 5)
        chunks = chunk_document(str(path))
        if not chunks:
            raise ValueError("No readable text or chunks were produced from the uploaded file.")
        update_stage(job_id, "chunking", "completed", f"Created {len(chunks)} chunks", 100)

        update_stage(job_id, "vector_store", "running", "Creating embeddings and saving source chunks", 10)
        chunk_ids = store_document_vectors(job_id, chunks)
        update_stage(job_id, "vector_store", "completed", f"Stored {len(chunks)} searchable chunks", 100)

        update_stage(job_id, "fact_extraction", "running", f"Sending 0 of {len(chunks)} chunks to {OLLAMA_MODEL}", 0)
        fact_count = extract_document_facts(job_id, chunk_ids, chunks)
        update_stage(job_id, "fact_extraction", "completed", f"Saved {fact_count} extracted facts (attempted)", 100)

        update_stage(job_id, "ontology", "running", "Deriving types and relationships from extracted facts", 10)
        node_count, relationship_count = derive_ontology_for_document(chunk_ids)
        update_stage(job_id, "ontology", "completed", f"Observed {node_count} entity types and {relationship_count} relationship types", 100)

        update_stage(job_id, "graph", "running", "Loading facts into Neo4j (optional)", 10)
        try:
            detail = build_graph_if_available()
            update_stage(job_id, "graph", "completed", detail, 100)
        except Exception as exc:
            # Neo4j is a projection. Vector and fact queries remain useful without it.
            update_stage(job_id, "graph", "skipped", f"Neo4j unavailable: {exc}", 100)
        with jobs_lock:
            jobs[job_id]["state"] = "completed"
            jobs[job_id]["updated_at"] = now()
    except Exception as exc:
        with jobs_lock:
            jobs[job_id]["state"] = "failed"
            jobs[job_id]["error"] = str(exc)
            jobs[job_id]["updated_at"] = now()


async def run_pipeline(job_id: str, path: Path) -> None:
    await asyncio.to_thread(run_pipeline_sync, job_id, path)


def scroll_points(client: QdrantClient, document_id: str | None = None) -> list[Any]:
    points, offset = [], None
    while True:
        batch, offset = client.scroll(COLLECTION_NAME, offset=offset, limit=128, with_payload=True, with_vectors=True)
        points.extend(point for point in batch if not document_id or point.payload.get("document_id") == document_id)
        if offset is None:
            return points


def cosine(a: list[float], b: list[float]) -> float:
    numerator = sum(x * y for x, y in zip(a, b))
    denominator = (sum(x * x for x in a) * sum(y * y for y in b)) ** 0.5
    return numerator / denominator if denominator else 0.0


def related_facts(question: str, document_id: str | None) -> list[dict[str, Any]]:
    terms = [term for term in re.findall(r"\w+", question.lower()) if len(term) > 2][:8]
    if not terms:
        return []
    conn = facts.get_connection()
    cursor = conn.cursor()
    try:
        if document_id:
            # Fact rows reference the UUID point ids stored for this document.
            point_ids = [str(point.id) for point in scroll_points(qdrant_client(), document_id)]
            if not point_ids:
                return []
            cursor.execute("""SELECT source_chunk_id, subject, relationship, object, confidence
                FROM extracted_facts WHERE source_chunk_id = ANY(%s)""", (point_ids,))
        else:
            cursor.execute("SELECT source_chunk_id, subject, relationship, object, confidence FROM extracted_facts")
        rows = cursor.fetchall()
        selected = []
        for source, subject, relationship, obj, confidence in rows:
            haystack = f"{subject} {relationship} {obj}".lower()
            if any(term in haystack for term in terms):
                selected.append({"source_chunk_id": source, "subject": subject, "relationship": relationship, "object": obj, "confidence": confidence})
        return selected[:12]
    except psycopg2.Error:
        return []
    finally:
        cursor.close(); conn.close()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(UI_FILE)


@app.post("/api/documents", status_code=202)
async def upload_and_start(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    UPLOAD_DIR.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename).name)
    job = new_job(safe_name)
    stored_path = UPLOAD_DIR / f"{job['id']}_{safe_name}"
    with stored_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    with jobs_lock:
        jobs[job["id"]] = job
    asyncio.create_task(run_pipeline(job["id"], stored_path))
    return {"document_id": job["id"], "status_url": f"/api/jobs/{job['id']}"}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    try:
        return public_job(job_id)
    except KeyError:
        raise HTTPException(404, "Unknown document/job ID")


@app.post("/api/query")
def query(request: QueryRequest) -> dict[str, Any]:
    question = request.question.strip()
    if not question:
        raise HTTPException(400, "A question is required.")
    try:
        client = qdrant_client()
        query_vector = create_embeddings([question])[0].tolist()
        points = scroll_points(client, request.document_id)
    except Exception as exc:
        raise HTTPException(503, f"Search is not ready: {exc}")
    ranked = sorted(points, key=lambda point: cosine(query_vector, point.vector), reverse=True)[:5]
    contexts = [{"chunk_id": str(point.id), "filename": point.payload.get("filename"), "text": point.payload.get("text", ""), "score": round(cosine(query_vector, point.vector), 3)} for point in ranked]
    structured = related_facts(question, request.document_id)
    if not contexts:
        state = "No source chunks are available yet. Upload processing may still be in chunking/embedding."
        return {"answer": state, "sources": [], "facts": structured}
    evidence = "\n\n".join(f"[Chunk {item['chunk_id']}] {item['text']}" for item in contexts)
    fact_text = "\n".join(f"{f['subject']} --{f['relationship']}--> {f['object']}" for f in structured) or "No matching structured facts are ready."
    prompt = f"""Answer only from the supplied source chunks and extracted facts. If the answer is not supported, say so. Be concise and cite chunk IDs in square brackets.\n\nQuestion: {question}\n\nExtracted facts:\n{fact_text}\n\nSource chunks:\n{evidence}"""
    try:
        with ollama_lock:
            response = ollama_client.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], options={"temperature": 0})
        answer = response["message"]["content"]
    except Exception as exc:
        answer = f"Relevant source chunks were found, but the local LLM is unavailable: {exc}"
    return {"answer": answer, "sources": contexts, "facts": structured}
