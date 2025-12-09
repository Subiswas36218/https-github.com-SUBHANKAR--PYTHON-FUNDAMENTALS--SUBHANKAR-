import pandas as pd
from qdrant_client.models import PointStruct

from src.models.chunk import ScientificArticleChunk
from src.storage.vector import COLLECTION_NAME, client


def insert_embeddings(article: pd.Series) -> pd.Series:
    i = 0
    for text, emb in zip(article.chunk_texts, article.embeddings, strict=True):
        point = PointStruct(
            id=f"{article.arxiv_id}_chunk_{i}",
            vector=emb,
            payload=ScientificArticleChunk(
                title=article.title,
                summary=article.summary,
                arxiv_id=article.arxiv_id,
                author_full_name=article.author_full_name,
                chunk_text=text,
                chunk_index=i,
            ).model_dump(),
        )
        client.upsert(collection_name=COLLECTION_NAME, points=[point])
        i += 1


def save_to_qdrant(df: pd.DataFrame) -> pd.DataFrame:
    df.apply(insert_embeddings, axis=1)
    return df
