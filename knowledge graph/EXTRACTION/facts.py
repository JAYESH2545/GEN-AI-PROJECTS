import json
import re
import psycopg2
import ollama

from qdrant_client import QdrantClient
from pydantic import BaseModel
from typing import List



# DATABASE CONFIG


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "graphrag",
    "user": "postgres",
    "password": "postgres"
}



# QDRANT CONFIG


QDRANT_URL = "http://localhost:6333"

QDRANT_COLLECTION = "documents"

TEXT_FIELD = "text"



# OLLAMA CONFIG


OLLAMA_MODEL = "qwen2.5:7b"



# QDRANT CLIENT


qdrant = QdrantClient(
    url=QDRANT_URL
)



# STRUCTURED FACT MODEL


class ExtractedFact(BaseModel):

    subject: str

    subject_type: str

    relationship: str

    object: str

    object_type: str

    confidence: float


class FactExtractionResult(BaseModel):

    facts: List[ExtractedFact]



# POSTGRES CONNECTION


def get_connection():

    return psycopg2.connect(
        **DB_CONFIG
    )



# CREATE FACT TABLE


def create_fact_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_facts (

            id SERIAL PRIMARY KEY,

            source_chunk_id VARCHAR(255),

            subject VARCHAR(255) NOT NULL,

            subject_type VARCHAR(100) NOT NULL,

            relationship VARCHAR(100) NOT NULL,

            object VARCHAR(255) NOT NULL,

            object_type VARCHAR(100) NOT NULL,

            confidence FLOAT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                source_chunk_id,
                subject,
                relationship,
                object
            )
        );
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Fact table ready.")



# READ CHUNKS FROM QDRANT


def get_chunks_from_qdrant():

    print("\nReading chunks from Qdrant...")

    all_points = []

    offset = None

    while True:

        points, next_offset = qdrant.scroll(

            collection_name=QDRANT_COLLECTION,

            limit=100,

            offset=offset,

            with_payload=True,

            with_vectors=False
        )

        all_points.extend(points)

        if next_offset is None:
            break

        offset = next_offset


    print(
        f"Found {len(all_points)} chunks in Qdrant."
    )


    chunks = []

    for point in all_points:

        payload = point.payload or {}

        text = payload.get(
            TEXT_FIELD
        )

        if not text:
            continue

        chunks.append({

            "id": str(point.id),

            "text": text
        })


    print(
        f"Found {len(chunks)} chunks containing text."
    )

    return chunks



# EXTRACT FACTS FROM ONE CHUNK


def extract_facts_from_chunk(chunk_text):

    prompt = f"""
You are a generic knowledge graph fact extraction system.

Your job is to extract factual relationships from a document chunk.

The document can be ANY type of document.

Examples:

- college syllabus
- technical documentation
- research paper
- business document
- legal document
- product documentation
- book
- report
- financial document
- scientific document
- any other text

IMPORTANT:

Do NOT assume a predefined ontology.

Discover the entity types and relationships from the actual text.

DOCUMENT CHUNK:

-------------------------
{chunk_text}
-------------------------

EXTRACTION RULES:

1. Extract ONLY facts explicitly supported by the text.

2. NEVER invent information.

3. Identify meaningful entities.

4. Give each entity a useful type.

Examples of possible entity types:

Person
Company
University
Organization
Course
Subject
Semester
Department
Topic
Technology
Software
Database
Concept
Location
Event
Document
Product
Project
Exam
Skill

These are examples only.

You may create another entity type when necessary.

5. Relationship names must:

- be concise
- be uppercase
- use underscores between words

Examples:

HAS_TOPIC
CONTAINS
USES
SUPPORTS
LOCATED_IN
AUTHORED
WORKS_AT
PREREQUISITE_OF
PART_OF
HAS_COURSE
HAS_SUBJECT
OFFERED_IN
HAS_CREDIT
BELONGS_TO

These are examples only.

6. Do NOT create relationships that are not supported by the text.

7. Do NOT extract meaningless relationships.

8. If the chunk contains no meaningful relationships, return:

{{
    "facts": []
}}

9. Confidence must be a number between 0 and 1.

10. Prefer specific entities over vague entities.

11. Keep entity names concise.

12. Do not duplicate the same fact.

13. Return ONLY JSON.

Required JSON structure:

{{
    "facts": [
        {{
            "subject": "entity name",
            "subject_type": "entity type",
            "relationship": "RELATIONSHIP",
            "object": "entity name",
            "object_type": "entity type",
            "confidence": 0.95
        }}
    ]
}}
"""


    def parse_response(content):
        """Parse strict JSON, including JSON wrapped in a markdown fence."""
        candidates = [content.strip()]
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.IGNORECASE | re.DOTALL)
        if fenced:
            candidates.append(fenced.group(1).strip())

        for candidate in candidates:
            try:
                return FactExtractionResult.model_validate(json.loads(candidate))
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        raise ValueError("Ollama returned invalid or truncated JSON")

    last_error = None
    content = ""
    for attempt in range(1, 4):
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt + (
                        "\n\nReturn a complete JSON object now. Do not use markdown or commentary."
                        if attempt > 1 else ""
                    )
                }
            ],
            format=FactExtractionResult.model_json_schema(),
            options={"temperature": 0}
        )
        content = response["message"]["content"]
        try:
            result = parse_response(content)
            break
        except ValueError as error:
            last_error = error
            print(f"Could not parse Ollama response (attempt {attempt}/3). Retrying...")
    else:
        print("\nRaw Ollama response:")
        print(content)
        raise last_error


    
    # Validate confidence values
    

    for fact in result.facts:

        if fact.confidence < 0:

            fact.confidence = 0.0

        if fact.confidence > 1:

            fact.confidence = 1.0


    return result



# INSERT FACT


def insert_fact(
    cursor,
    chunk_id,
    fact
):

    cursor.execute("""

        INSERT INTO extracted_facts (

            source_chunk_id,

            subject,

            subject_type,

            relationship,

            object,

            object_type,

            confidence

        )

        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s

        )

        ON CONFLICT (

            source_chunk_id,
            subject,
            relationship,
            object

        )

        DO NOTHING;

    """,

    (

        chunk_id,

        fact.subject,

        fact.subject_type,

        fact.relationship,

        fact.object,

        fact.object_type,

        fact.confidence

    ))



# PROCESS ALL CHUNKS


def process_chunks():

    chunks = get_chunks_from_qdrant()


    if not chunks:

        print("\nNo chunks found.")

        print(
            "Check your Qdrant collection name and TEXT_FIELD."
        )

        return


    conn = get_connection()

    cursor = conn.cursor()


    total_facts = 0


    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"\nProcessing chunk "
            f"{index}/{len(chunks)}..."
        )


        try:

            result = extract_facts_from_chunk(
                chunk["text"]
            )


            print(
                f"Extracted "
                f"{len(result.facts)} facts."
            )


            for fact in result.facts:

                insert_fact(

                    cursor,

                    chunk["id"],

                    fact
                )


                print(

                    f"  "
                    f"{fact.subject}"
                    f" [{fact.subject_type}]"
                    f" --{fact.relationship}--> "
                    f"{fact.object}"
                    f" [{fact.object_type}]"
                    f" "
                    f"(confidence: "
                    f"{fact.confidence:.2f})"

                )


                total_facts += 1


            conn.commit()


        except Exception as e:

            print(
                f"ERROR processing chunk "
                f"{chunk['id']}:"
            )

            print(e)

            conn.rollback()


    cursor.close()

    conn.close()


    print("\n" + "=" * 60)

    print(
        f"Total extracted facts: "
        f"{total_facts}"
    )

    print(
        "Facts saved to PostgreSQL."
    )

    print("=" * 60)



# SHOW DATABASE FACTS


def show_facts():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

        SELECT

            id,

            subject,

            subject_type,

            relationship,

            object,

            object_type,

            confidence

        FROM extracted_facts

        ORDER BY id;

    """)


    rows = cursor.fetchall()


    print("\n")

    print("=" * 80)

    print("FACTS IN POSTGRESQL")

    print("=" * 80)


    for row in rows:

        print(

            f"\n{row[1]} "
            f"[{row[2]}]"
            f" --{row[3]}--> "
            f"{row[4]} "
            f"[{row[5]}]"

        )

        print(
            f"Confidence: {row[6]}"
        )


    print(
        f"\nTotal database facts: "
        f"{len(rows)}"
    )


    cursor.close()

    conn.close()



# CHECK OLLAMA


def check_ollama():

    print("\nChecking Ollama...")

    try:

        models = ollama.list()

        installed_models = []

        for model in models.models:

            installed_models.append(
                model.model
            )


        if not any(
            OLLAMA_MODEL in model
            for model in installed_models
        ):

            print(
                f"\nModel '{OLLAMA_MODEL}' "
                f"is not installed."
            )

            print(
                f"Run:\n"
                f"ollama pull {OLLAMA_MODEL}"
            )

            return False


        print(
            f"✓ Ollama is ready."
        )

        print(
            f"✓ Model: {OLLAMA_MODEL}"
        )

        return True


    except Exception as e:

        print(
            "\nCould not connect to Ollama."
        )

        print(e)

        print(
            "\nMake sure Ollama is installed "
            "and running."
        )

        return False



# MAIN


def main():

    print("=" * 60)

    print(
        "GENERIC KNOWLEDGE GRAPH "
        "FACT EXTRACTION"
    )

    print("=" * 60)


    
    # Check Ollama
    

    if not check_ollama():

        return


    
    # Create PostgreSQL table
    

    create_fact_table()


    
    # Extract facts
    

    process_chunks()


    
    # Display results
    

    show_facts()



# RUN


if __name__ == "__main__":

    main()
