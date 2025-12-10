import logging
import uuid

import numpy as np
import pandas as pd
from qdrant_client.models import PointStruct

from src.models.chunk import ScientificArticleChunk
from src.storage.vector import _CLIENT, COLLECTION_NAME

LOG = logging.getLogger(__name__)


def _get_base_id(article_chunk: pd.Series) -> str:
    """
    Choose a stable base ID for a chunk:
    - Prefer article_chunk.arxiv_id
    - Else article_chunk.id
    - Else a synthetic row-based ID
    """
    if "arxiv_id" in article_chunk and pd.notna(article_chunk["arxiv_id"]):
        return str(article_chunk["arxiv_id"])
    if "id" in article_chunk and pd.notna(article_chunk["id"]):
        return str(article_chunk["id"])
    return f"row-{article_chunk.name}"


def get_point_id(article_chunk: pd.Series) -> uuid.UUID:
    """
    Build a UUID from the arxiv/id + chunk_index so it is deterministic.
    """
    base = _get_base_id(article_chunk)
    idx = int(article_chunk.get("chunk_index", 0) or 0)
    raw = f"{base}_chunk_{idx}"
    return uuid.uuid5(uuid.NAMESPACE_URL, raw)


def check_if_chunk_exists(article_chunk: pd.Series) -> pd.Series:
    """
    Check if a given chunk already exists in Qdrant by point ID.
    """
    point_id = get_point_id(article_chunk)
    try:
        records = _CLIENT.retrieve(COLLECTION_NAME, ids=[point_id])
        exists = len(records) > 0
    except Exception as exc:
        LOG.error("Qdrant retrieve failed for %s: %s", point_id, exc)
        exists = False

    return pd.Series([exists], index=["exists_in_qdrant"], dtype=bool)


def insert_embedding(article_chunk: pd.Series) -> pd.Series:
    """
    Insert a single chunk row into Qdrant.

    Expects:
      - title
      - summary
      - arxiv_id or id
      - author_full_name (if available; empty otherwise)
      - chunk_text
      - chunk_index
      - embedding (np.ndarray)
    """
    embedding = getattr(article_chunk, "embedding", None)
    if embedding is None:
        return pd.Series([], index=[])

    if isinstance(embedding, np.ndarray):
        vector = embedding.astype(float).tolist()
    else:
        vector = list(embedding)  # best effort

    arxiv_id = getattr(
        article_chunk,
        "arxiv_id",
        getattr(article_chunk, "id", ""),
    )

    payload = ScientificArticleChunk(
        title=getattr(article_chunk, "title", ""),
        summary=getattr(article_chunk, "summary", ""),
        arxiv_id=str(arxiv_id),
        author_full_name=getattr(article_chunk, "author_full_name", ""),
        chunk_text=getattr(article_chunk, "chunk_text", ""),
        chunk_index=int(getattr(article_chunk, "chunk_index", 0) or 0),
    ).model_dump()

    point = PointStruct(
        id=get_point_id(article_chunk),
        vector=vector,
        payload=payload,
    )

    _CLIENT.upsert(collection_name=COLLECTION_NAME, points=[point])

    return pd.Series([], index=[])


def save_to_qdrant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Insert all chunks (rows) into Qdrant.
    """
    if df.empty:
        return df

    df.apply(insert_embedding, axis=1)
    return df


def check_chunks_in_qdrant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an 'exists_in_qdrant' boolean column per chunk row.
    """
    if df.empty:
        return df

    exists = df.apply(check_if_chunk_exists, axis=1)
    return pd.concat([df.reset_index(drop=True), exists.reset_index(drop=True)], axis=1)
