import os
import sys
import json
import time

from typing import List

import psycopg2
import ollama
from pydantic import BaseModel
from neo4j import GraphDatabase


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# PostgreSQL
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "graphrag",
    "user": "postgres",
    "password": "postgres"
}


def get_connection():

    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# Neo4j
# ============================================================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USER,
        NEO4J_PASSWORD
    )
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_MODEL = "qwen3:8b"

# Local model calls have no network layer to time out on their own.
OLLAMA_TIMEOUT = 120

RETRIES = 3

ollama_client = ollama.Client(timeout=OLLAMA_TIMEOUT)


# ============================================================
# Structured normalization output
# ============================================================

class NormalizedNode(BaseModel):

    original_name: str

    canonical_name: str

    description: str


class NormalizedRelationship(BaseModel):

    original_name: str

    canonical_name: str

    source_type: str

    target_type: str

    description: str


class NormalizedOntology(BaseModel):

    nodes: List[NormalizedNode]

    relationships: List[NormalizedRelationship]


# ============================================================
# READ ONTOLOGY FROM POSTGRESQL
# ============================================================

def read_ontology():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            name,
            description

        FROM ontology_nodes

        ORDER BY name;
    """)

    nodes = cursor.fetchall()

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            name,
            source_node,
            target_node,
            description

        FROM ontology_relationships

        ORDER BY name;
    """)

    relationships = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "nodes": nodes,
        "relationships": relationships
    }


# ============================================================
# NORMALIZE ONTOLOGY
# ============================================================

def normalize_ontology(ontology):

    nodes_text = ""

    for name, description in ontology["nodes"]:

        nodes_text += (
            f"NAME: {name}\n"
            f"DESCRIPTION: {description}\n\n"
        )


    relationships_text = ""

    for (
        name,
        source,
        target,
        description
    ) in ontology["relationships"]:

        relationships_text += (
            f"RELATIONSHIP: {name}\n"
            f"SOURCE: {source}\n"
            f"TARGET: {target}\n"
            f"DESCRIPTION: {description}\n\n"
        )


    prompt = f"""
You are an ontology normalization system.

You are given a candidate ontology extracted from a document.

Your job is to normalize it into a clean canonical ontology.

==================================================
ENTITY TYPES
==================================================

{nodes_text}

==================================================
RELATIONSHIPS
==================================================

{relationships_text}

==================================================
NORMALIZATION RULES
==================================================

1. Merge entity types that clearly represent the same concept.

Example:

Database
DB
DatabaseSystem

may become:

Database

2. Do NOT merge concepts merely because they are related.

For example:

Person
Employee

should not automatically become the same type.

3. Keep the most precise useful concept.

4. Entity type names must be singular.

Examples:

Customers -> Customer
Databases -> Database

5. Entity type names should be concise.

6. Relationship names must be uppercase.

Examples:

works at -> WORKS_AT
uses -> USES
created by -> CREATED_BY

7. Preserve relationship direction.

8. If two relationships clearly mean the same thing,
merge them.

9. Do not invent completely new entity types.

10. Do not invent relationships that were not present
in the input ontology.

11. Every relationship source_type must match one of
the canonical entity types.

12. Every relationship target_type must match one of
the canonical entity types.

Return only the normalized ontology.
"""


    last_error = None

    for attempt in range(RETRIES):

        try:

            response = ollama_client.chat(

                model=OLLAMA_MODEL,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                format=NormalizedOntology.model_json_schema(),

                options={
                    "temperature": 0
                }
            )

            content = response["message"]["content"]

            data = json.loads(content)

            return NormalizedOntology.model_validate(data)

        except Exception as e:

            last_error = e

            print(
                f"  Ollama call failed "
                f"(attempt {attempt + 1}/{RETRIES}): {e}"
            )

            if attempt < RETRIES - 1:
                time.sleep(2 * (attempt + 1))

    raise RuntimeError(
        f"Ontology normalization failed after {RETRIES} attempts"
    ) from last_error


# ============================================================
# CREATE NEO4J CONSTRAINTS
# ============================================================

def create_constraints():

    with neo4j_driver.session() as session:

        session.run("""
            CREATE CONSTRAINT ontology_entity_type_name IF NOT EXISTS
            FOR (n:OntologyEntityType)
            REQUIRE n.name IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT ontology_relationship_type_name IF NOT EXISTS
            FOR (n:OntologyRelationshipType)
            REQUIRE n.name IS UNIQUE
        """)

    print("Neo4j constraints created.")


# ============================================================
# CLEAR OLD ONTOLOGY
# ============================================================

def clear_old_ontology():

    with neo4j_driver.session() as session:

        session.run("""
            MATCH (n:OntologyEntityType)
            DETACH DELETE n
        """)

        session.run("""
            MATCH (n:OntologyRelationshipType)
            DETACH DELETE n
        """)

    print("Old ontology removed.")


# ============================================================
# SAVE ONTOLOGY TO NEO4J
# ============================================================

def save_ontology_to_neo4j(
    normalized
):

    with neo4j_driver.session() as session:

        # ----------------------------------------------------
        # Entity types
        # ----------------------------------------------------

        for node in normalized.nodes:

            session.run(
                """
                MERGE (
                    n:OntologyEntityType {
                        name: $name
                    }
                )

                SET
                    n.description = $description,
                    n.original_name = $original_name
                """,

                name=node.canonical_name,
                description=node.description,
                original_name=node.original_name
            )


        # ----------------------------------------------------
        # Relationship types
        # ----------------------------------------------------

        for relationship in normalized.relationships:

            session.run(
                """
                MERGE (
                    r:OntologyRelationshipType {
                        name: $name
                    }
                )

                SET
                    r.description = $description,
                    r.original_name = $original_name

                WITH r

                MATCH (
                    source:OntologyEntityType {
                        name: $source_type
                    }
                )

                MATCH (
                    target:OntologyEntityType {
                        name: $target_type
                    }
                )

                MERGE (
                    source
                    -[:ALLOWS_SOURCE]->
                    r
                    -[:ALLOWS_TARGET]->
                    target
                )
                """,

                name=relationship.canonical_name,

                description=relationship.description,

                original_name=relationship.original_name,

                source_type=relationship.source_type,

                target_type=relationship.target_type
            )

    print("Ontology successfully saved to Neo4j.")


# ============================================================
# DISPLAY NORMALIZED ONTOLOGY
# ============================================================

def print_normalized_ontology(
    normalized
):

    print("\n")
    print("=" * 60)
    print("NORMALIZED ONTOLOGY")
    print("=" * 60)

    print("\nENTITY TYPES:")

    for node in normalized.nodes:

        print(
            f"\n{node.original_name}"
            f"  -->  "
            f"{node.canonical_name}"
        )

        print(
            f"    {node.description}"
        )


    print("\nRELATIONSHIPS:")

    for relationship in normalized.relationships:

        print(
            f"\n{relationship.original_name}"
            f"  -->  "
            f"{relationship.canonical_name}"
        )

        print(
            f"    "
            f"{relationship.source_type}"
            f" -> "
            f"{relationship.target_type}"
        )


# ============================================================
# CHECK OLLAMA
# ============================================================

def check_ollama():

    print("\nChecking Ollama...")

    try:

        models = ollama.list()

        installed_models = [model.model for model in models.models]

        if not any(OLLAMA_MODEL in model for model in installed_models):

            print(f"\nModel '{OLLAMA_MODEL}' is not installed.")
            print(f"Run:\nollama pull {OLLAMA_MODEL}")

            return False

        print("✓ Ollama is ready.")
        print(f"✓ Model: {OLLAMA_MODEL}")

        return True

    except Exception as e:

        print("\nCould not connect to Ollama.")
        print(e)
        print("\nMake sure Ollama is installed and running.")

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    if not check_ollama():
        return

    print("\nReading ontology from PostgreSQL...")

    ontology = read_ontology()

    print(
        f"Found {len(ontology['nodes'])} "
        f"entity types."
    )

    print(
        f"Found {len(ontology['relationships'])} "
        f"relationships."
    )


    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    print("\nNormalizing ontology...")

    normalized = normalize_ontology(
        ontology
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print_normalized_ontology(
        normalized
    )


    # --------------------------------------------------------
    # Neo4j
    # --------------------------------------------------------

    print("\nConnecting to Neo4j...")

    create_constraints()

    clear_old_ontology()

    save_ontology_to_neo4j(
        normalized
    )


    print("\n")
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":

    try:

        main()

    finally:

        neo4j_driver.close()