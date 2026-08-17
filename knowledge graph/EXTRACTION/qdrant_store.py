from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from embedding import process_uploaded_documents


# ==========================================
# QDRANT CONFIGURATION
# ==========================================

COLLECTION_NAME = "documents"

# Connect to Docker Qdrant
client = QdrantClient(
    url="http://localhost:6333"
)


# ==========================================
# CREATE COLLECTION
# ==========================================

def create_collection():

    collections = client.get_collections()

    existing_collections = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME not in existing_collections:

        client.create_collection(

            collection_name=COLLECTION_NAME,

            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

        print("✓ Qdrant collection created")

    else:

        print("✓ Qdrant collection already exists")


# ==========================================
# STORE EMBEDDINGS
# ==========================================

def store_embeddings(results):

    points = []

    for index, item in enumerate(results):

        point = PointStruct(

            id=index,

            vector=item["embedding"],

            payload={
                "chunk_id": item["chunk_id"],
                "text": item["text"]
            }
        )

        points.append(point)

    client.upsert(

        collection_name=COLLECTION_NAME,

        points=points
    )

    print(
        f"✓ Stored {len(points)} vectors in Qdrant"
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    print("=" * 60)
    print("EMBEDDING + QDRANT PIPELINE")
    print("=" * 60)

    # Check Qdrant connection
    try:

        collections = client.get_collections()

        print("✓ Connected to Qdrant at localhost:6333")

    except Exception as e:

        print("✗ Could not connect to Qdrant")
        print(e)
        exit(1)


    # Create collection
    create_collection()


    # Generate embeddings
    print()
    print("Generating embeddings...")

    results = process_uploaded_documents()


    if not results:

        print("No documents found.")

    else:

        # Store vectors
        store_embeddings(results)

        print()
        print("=" * 60)
        print("QDRANT STORAGE COMPLETE")
        print("=" * 60)

        print(
            f"Total vectors stored: {len(results)}"
        )