from neo4j import GraphDatabase


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"


class Neo4jLoader:

    def __init__(self):

        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(
                NEO4J_USER,
                NEO4J_PASSWORD
            )
        )

    def close(self):

        self.driver.close()

    def create_fact(
        self,
        subject,
        subject_type,
        relationship,
        object_name,
        object_type,
        confidence=None
    ):

        query = f"""
        MERGE (s:{subject_type} {{name: $subject}})

        MERGE (o:{object_type} {{name: $object_name}})

        MERGE (s)-[r:{relationship}]->(o)

        SET r.confidence = $confidence
        """

        with self.driver.session() as session:

            session.run(
                query,
                subject=subject,
                object_name=object_name,
                confidence=confidence
            )

    def load_facts(self, facts):

        for fact in facts:

            self.create_fact(
                subject=fact["subject"],
                subject_type=fact["subject_type"],
                relationship=fact["relationship"],
                object_name=fact["object"],
                object_type=fact["object_type"],
                confidence=fact["confidence"]
            )