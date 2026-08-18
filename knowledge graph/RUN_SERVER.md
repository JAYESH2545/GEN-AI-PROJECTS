# Run the Local GraphRAG server

Open PowerShell in this project folder and activate the same virtual environment
that already runs the existing extraction scripts. Then install the web-server
requirements:

```powershell
pip install -r requirements-api.txt
```

Start the local services first:

```powershell
# Docker Desktop must say "Engine running" before this command.
docker start qdrant

# Start PostgreSQL and Neo4j if you want facts and the graph stages.
# Start Ollama, then make sure the extractor's configured model is present.
ollama serve
ollama pull qwen2.5:7b
```

In a second PowerShell window, start the application:

```powershell
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. Upload a TXT, PDF, or DOCX file. The page shows
the state of each pipeline stage. You may ask questions after the **vector
store** stage is complete; facts and the ontology will continue in the
background.

The browser opens automatically when the server starts. To prevent that (for
example on a remote machine), use `$env:OPEN_BROWSER=0` before starting Uvicorn.

## What must be running

| Service | Address | Used for |
| --- | --- | --- |
| Qdrant | `http://localhost:6333` | chunks and vector search |
| PostgreSQL | `localhost:5432/graphrag` | incrementally saved facts and ontology |
| Ollama | local default endpoint | Qwen fact extraction and answers |
| Neo4j (optional) | `bolt://localhost:7687` | graph projection only |

If Neo4j is unavailable, its stage is marked **skipped** and document search,
facts, and answers continue to work. If Qdrant, PostgreSQL, or Ollama is
unavailable, the job status displays the exact failed stage and error.

The configuration still comes from the existing project files: database values
are in `EXTRACTION/facts.py` and `ONTOLOGY/ontology.py`; the Ollama model is
`qwen2.5:7b` in `EXTRACTION/facts.py`. Change those values there if your local
setup differs.
