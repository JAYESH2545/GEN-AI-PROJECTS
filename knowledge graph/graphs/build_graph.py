from neo4j import GraphDatabase

from postgres_reader import get_facts


# ============================================================
# Neo4j configuration
# ============================================================

NEO4J_URI = "bolt://localhost:7687"

NEO4J_USER = "neo4j"

NEO4J_PASSWORD = "password"


# ============================================================
# Neo4j connection
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USER,
        NEO4J_PASSWORD
    )
)


# ============================================================
# Create graph
# ============================================================

def create_fact(
    tx,
    fact
):

    query = """
    MERGE (subject:Entity {
        name: $subject
    })

    SET
        subject.type = $subject_type

    MERGE (object:Entity {
        name: $object
    })

    SET
        object.type = $object_type

    MERGE (
        subject
    )-[r:RELATION {
        type: $relationship
    }]->(
        object
    )

    SET
        r.confidence = $confidence,
        r.source_chunk_id = $source_chunk_id
    """

    tx.run(
        query,

        subject=fact["subject"],

        subject_type=fact["subject_type"],

        object=fact["object"],

        object_type=fact["object_type"],

        relationship=fact["relationship"],

        confidence=fact["confidence"],

        source_chunk_id=fact["source_chunk_id"]
    )


# ============================================================
# Build graph
# ============================================================

def build_graph():

    print("Reading facts from PostgreSQL...")

    facts = get_facts()

    print(
        f"Found {len(facts)} facts."
    )

    if not facts:

        print(
            "No facts found in PostgreSQL."
        )

        return

    print("Connecting to Neo4j...")

    with driver.session() as session:

        for fact in facts:

            print(
                f"{fact['subject']} "
                f"--{fact['relationship']}--> "
                f"{fact['object']}"
            )

            session.execute_write(
                create_fact,
                fact
            )

    print(
        "\nGraph created successfully."
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    try:

        build_graph()

    finally:

        driver.close()