import psycopg2


# ============================================================
# PostgreSQL configuration
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "graphrag",
    "user": "postgres",
    "password": "postgres"
}


# ============================================================
# Database connection
# ============================================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# Create ontology tables
# ============================================================

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Node types
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ontology_nodes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT
        );
    """)

    # --------------------------------------------------------
    # Relationship types
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ontology_relationships (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            source_node VARCHAR(100) NOT NULL,
            target_node VARCHAR(100) NOT NULL,
            description TEXT,

            UNIQUE(
                name,
                source_node,
                target_node
            )
        );
    """)

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ontology_properties (
            id SERIAL PRIMARY KEY,
            node_name VARCHAR(100) NOT NULL,
            property_name VARCHAR(100) NOT NULL,
            data_type VARCHAR(50) NOT NULL,
            required BOOLEAN DEFAULT FALSE,
            description TEXT,

            UNIQUE(
                node_name,
                property_name
            )
        );
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Ontology tables created successfully.")


# ============================================================
# Insert ontology
# ============================================================

def insert_ontology():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Node types
    # --------------------------------------------------------

    nodes = [

        (
            "Person",
            "A human being."
        ),

        (
            "Company",
            "A business organization."
        ),

        (
            "Document",
            "An uploaded source document."
        ),

        (
            "Chunk",
            "A section of a document."
        )
    ]

    for name, description in nodes:

        cursor.execute("""
            INSERT INTO ontology_nodes
                (name, description)

            VALUES
                (%s, %s)

            ON CONFLICT (name)
            DO NOTHING;
        """, (
            name,
            description
        ))

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    relationships = [

        (
            "FOUNDED",
            "Person",
            "Company",
            "A person founded a company."
        ),

        (
            "WORKS_AT",
            "Person",
            "Company",
            "A person works at a company."
        ),

        (
            "ACQUIRED",
            "Company",
            "Company",
            "One company acquired another company."
        ),

        (
            "CEO_OF",
            "Person",
            "Company",
            "A person is the CEO of a company."
        )
    ]

    for (
        name,
        source,
        target,
        description
    ) in relationships:

        cursor.execute("""
            INSERT INTO ontology_relationships
                (
                    name,
                    source_node,
                    target_node,
                    description
                )

            VALUES
                (%s, %s, %s, %s)

            ON CONFLICT (
                name,
                source_node,
                target_node
            )

            DO NOTHING;
        """, (
            name,
            source,
            target,
            description
        ))

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    properties = [

        # Person
        (
            "Person",
            "name",
            "string",
            True,
            "Person's name."
        ),

        (
            "Person",
            "birth_year",
            "integer",
            False,
            "Year the person was born."
        ),

        # Company
        (
            "Company",
            "name",
            "string",
            True,
            "Company name."
        ),

        (
            "Company",
            "founded_year",
            "integer",
            False,
            "Year the company was founded."
        ),

        (
            "Company",
            "industry",
            "string",
            False,
            "Company industry."
        ),

        # Document
        (
            "Document",
            "filename",
            "string",
            True,
            "Original uploaded filename."
        ),

        # Chunk
        (
            "Chunk",
            "text",
            "string",
            True,
            "Text contained in the chunk."
        )
    ]

    for (
        node,
        prop,
        data_type,
        required,
        description
    ) in properties:

        cursor.execute("""
            INSERT INTO ontology_properties
                (
                    node_name,
                    property_name,
                    data_type,
                    required,
                    description
                )

            VALUES
                (%s, %s, %s, %s, %s)

            ON CONFLICT (
                node_name,
                property_name
            )

            DO NOTHING;
        """, (
            node,
            prop,
            data_type,
            required,
            description
        ))

    conn.commit()

    cursor.close()
    conn.close()

    print("Ontology inserted successfully.")


# ============================================================
# READ ONTOLOGY
# ============================================================

def get_ontology():

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

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            node_name,
            property_name,
            data_type,
            required,
            description

        FROM ontology_properties

        ORDER BY node_name, property_name;
    """)

    properties = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "nodes": nodes,
        "relationships": relationships,
        "properties": properties
    }


# ============================================================
# Test ontology
# ============================================================

if __name__ == "__main__":

    create_tables()

    insert_ontology()

    ontology = get_ontology()

    print("\n==============================")
    print("ONTOLOGY")
    print("==============================")

    print("\nNODE TYPES:")

    for node in ontology["nodes"]:
        print(
            f"{node[0]} -> {node[1]}"
        )

    print("\nRELATIONSHIPS:")

    for relationship in ontology["relationships"]:

        print(
            f"{relationship[0]}: "
            f"{relationship[1]} -> "
            f"{relationship[2]}"
        )

    print("\nPROPERTIES:")

    for prop in ontology["properties"]:

        print(
            f"{prop[0]}.{prop[1]} "
            f"({prop[2]})"
        )