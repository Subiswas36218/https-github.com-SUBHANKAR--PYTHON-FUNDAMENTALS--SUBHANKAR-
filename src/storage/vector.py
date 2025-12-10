from __future__ import annotations

from typing import Final

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME: Final[str] = "scientific_articles"
VECTOR_SIZE: Final[int] = 768


def get_qdrant_client(host: str = "localhost", port: int = 6333) -> QdrantClient:
    """Return a Qdrant client connected to the local Docker container."""
    return QdrantClient(host=host, port=port)


def ensure_collection(
    client: QdrantClient | None = None,
) -> QdrantClient:
    """
    Ensure the vector collection exists, creating it if needed.

    Returns the client so you can chain calls:
        client = ensure_collection()
    """
    if client is None:
        client = get_qdrant_client()

    collections = client.get_collections().collections or []
    existing = {c.name for c in collections}

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

    return client


__all__ = [
    "COLLECTION_NAME",
    "VECTOR_SIZE",
    "get_qdrant_client",
    "ensure_collection",
]
