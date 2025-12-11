from qdrant_client.models import ScoredPoint

from src.storage.vector import _CLIENT, COLLECTION_NAME
from src.utils.embed import embed
from src.utils.timeit import timeit


@timeit("Search qdrant")
def search_qdrant(query: str) -> list[ScoredPoint]:
    query_vector = embed(query, task_type="RETRIEVAL_QUERY")
    results = _CLIENT.query_points(COLLECTION_NAME, query_vector, with_payload=True)
    return results.points


if __name__ == "__main__":
    results = search_qdrant(
        "What we can do in order to obtain a fast"
        "approximation up to order 2 of Landau tail?"
    )
    for point in results:
        chunk_text = (point.payload or {})["chunk_text"]
        print(f"Score: {point.score}\n{chunk_text}")
        print("-" * 50)
