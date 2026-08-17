import psycopg2


# ============================================================
# POSTGRESQL CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "graphrag",
    "user": "postgres",
    "password": "postgres"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# CREATE FACT TABLE
# ============================================================

def create_fact_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_facts (

            id SERIAL PRIMARY KEY,

            source_chunk_id VARCHAR(255),

            subject TEXT NOT NULL,
            subject_type VARCHAR(100),

            relationship VARCHAR(150) NOT NULL,

            object TEXT NOT NULL,
            object_type VARCHAR(100),

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

    print("✓ Fact table ready.")


# ============================================================
# SAVE ONE FACT
# ============================================================

def save_fact(
    source_chunk_id,
    subject,
    subject_type,
    relationship,
    object_value,
    object_type,
    confidence=0.0
):

    conn = get_connection()
    cursor = conn.cursor()

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

        VALUES (%s, %s, %s, %s, %s, %s, %s)

        ON CONFLICT (
            source_chunk_id,
            subject,
            relationship,
            object
        )

        DO NOTHING;
    """, (
        source_chunk_id,
        subject,
        subject_type,
        relationship,
        object_value,
        object_type,
        confidence
    ))

    conn.commit()

    cursor.close()
    conn.close()


# ============================================================
# SAVE MULTIPLE FACTS
# ============================================================

def save_facts(facts):

    if not facts:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    saved = 0

    for fact in facts:

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

            VALUES (%s, %s, %s, %s, %s, %s, %s)

            ON CONFLICT (
                source_chunk_id,
                subject,
                relationship,
                object
            )

            DO NOTHING;
        """, (
            fact.get("source_chunk_id"),
            fact.get("subject"),
            fact.get("subject_type"),
            fact.get("relationship"),
            fact.get("object"),
            fact.get("object_type"),
            fact.get("confidence", 0.0)
        ))

        saved += cursor.rowcount

    conn.commit()

    cursor.close()
    conn.close()

    return saved


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    create_fact_table()

    print("✓ PostgreSQL fact storage is ready.")