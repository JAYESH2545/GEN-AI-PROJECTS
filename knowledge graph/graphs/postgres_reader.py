import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "graphrag",
    "user": "postgres",
    "password": "postgres"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_facts():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            source_chunk_id,
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

    cursor.close()
    conn.close()

    facts = []

    for row in rows:

        facts.append({

            "id": row[0],

            "source_chunk_id": row[1],

            "subject": row[2],
            "subject_type": row[3],

            "relationship": row[4],

            "object": row[5],
            "object_type": row[6],

            "confidence": row[7]
        })

    return facts