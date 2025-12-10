import uuid
from typing import Final

import pandas as pd
from qdrant_client.models import PointStruct

from src.models.chunk import ScientificArticleChunk
from src.storage.vector import COLLECTION_NAME, ensure_collection

# Reuse one client for the whole module
client = ensure_collection()
_BATCH_SIZE: Final[int] = 32  # optional, but handy if you later batch


def main() -> None:
    # Make sure the collection exists (already handled by the global `client`,
    # but keeping this for CLI use if you ever run `python -m src.usecases.vector`)
    ensure_collection()


if __name__ == "__main__":
    main()


def insert_embeddings(article: pd.Series) -> pd.Series:
    """
    Insert all chunk embeddings for a single article into Qdrant.

    Expects columns:
      - article.chunk_texts: list[str]
      - article.embeddings: 2D array-like (list[list[float]] or np.ndarray)
    """

    # Safety: if there are no embeddings, do nothing
    if not getattr(article, "chunk_texts", None) or not getattr(
        article, "embeddings", None
    ):
        return pd.Series([], index=[])

    # article.embeddings is likely a numpy array; convert row-wise to list
    points: list[PointStruct] = []
    for i, (text, emb) in enumerate(
        zip(article.chunk_texts, article.embeddings, strict=True)
    ):
        # Qdrant requires ID to be uint or UUID. Use a fresh UUID4.
        point_id = str(uuid.uuid4())

        point = PointStruct(
            id=point_id,
            vector=emb.tolist() if hasattr(emb, "tolist") else list(emb),
            payload=ScientificArticleChunk(
                title=article.title,
                summary=article.summary,
                arxiv_id=article.arxiv_id,
                author_full_name=article.author_full_name,
                chunk_text=text,
                chunk_index=i,
            ).model_dump(),
        )
        points.append(point)

    # Single upsert per article (can later batch across articles if needed)
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    # Nothing to merge back into the DataFrame
    return pd.Series([], index=[])


def save_to_qdrant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Iterate over rows and push their embeddings to Qdrant.
    """
    df.apply(insert_embeddings, axis=1)
    return df
