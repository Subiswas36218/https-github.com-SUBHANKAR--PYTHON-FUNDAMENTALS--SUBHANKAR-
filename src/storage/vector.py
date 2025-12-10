from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

_CLIENT = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "scientific_articles"

# Create collection only if it does NOT exist
if not _CLIENT.collection_exists(collection_name=COLLECTION_NAME):
    _CLIENT.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
