from __future__ import annotations

import logging
import os

import numpy as np
import pandas as pd
from google import genai
from google.genai import types
from tqdm.auto import tqdm

LOG = logging.getLogger(__name__)

tqdm.pandas(desc="Embedding articles")

_CLIENT: genai.Client | None = None
_EMBEDDING_DISABLED: bool = False  # set to True after quota errors


def get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Export it before running, e.g.\n\n"
            "  export GOOGLE_API_KEY='your-key-here'\n"
        )

    _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _empty_embedding_series() -> pd.Series:
    """Helper: consistent empty result."""
    return pd.Series(
        {
            "embedding": None,
        },
        index=["embedding"],
    )


def apply_chunking(
    article: pd.Series, chunk_size: int = 1000, overlap: int = 200
) -> pd.Series:
    """
    Split article.md_text into overlapping chunks.

    Returns a Series with:
      - chunk_text: list[str]
      - chunk_index: list[int]
    which will then be exploded by chunk_documents().
    """
    text = getattr(article, "md_text", "") or ""
    text = str(text)

    if not text:
        return pd.Series(
            {"chunk_text": [], "chunk_index": []},
            index=["chunk_text", "chunk_index"],
        )

    start = 0
    chunks: list[str] = []

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to cut on a sentence boundary if possible
        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        # avoid infinite loop if overlap > chunk_size
        start = max(end - overlap, end)

    return pd.Series(
        [chunks, list(range(len(chunks)))],
        index=["chunk_text", "chunk_index"],
    )


def embed_article(article_chunk: pd.Series) -> pd.Series:
    """
    Embed a single chunk row (after explode).
    Expects:
      - article_chunk.chunk_text : str
    Returns:
      - embedding: np.ndarray
    """
    global _EMBEDDING_DISABLED

    if _EMBEDDING_DISABLED:
        return _empty_embedding_series()

    text = getattr(article_chunk, "chunk_text", None)
    if not text:
        return _empty_embedding_series()

    try:
        client = get_client()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[text],
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="SEMANTIC_SIMILARITY",
            ),
        )
    except Exception as exc:  # quota, network, etc.
        LOG.error("embed_article failed: %s", exc)
        _EMBEDDING_DISABLED = True
        return _empty_embedding_series()

    if not result.embeddings:
        return _empty_embedding_series()

    return pd.Series(
        [np.array(result.embeddings[0].values, dtype=float)],
        index=["embedding"],
    )


def embed_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply embed_article to each row (each row is a chunk) and append 'embedding' column.
    """
    if df.empty:
        return df

    embedding_df = df.progress_apply(embed_article, axis=1)

    out = pd.concat(
        [df.reset_index(drop=True), embedding_df.reset_index(drop=True)],
        axis=1,
    )

    num_ok = out["embedding"].notna().sum()
    num_total = len(out)
    LOG.info("embed_documents: %d/%d rows have embeddings", num_ok, num_total)

    return out


def chunk_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Turn each article into multiple chunk rows.

    Input: one row per article, with 'md_text'.
    Output: multiple rows per article, with columns:
      - chunk_index (int)
      - chunk_text  (str)
    """
    if df.empty:
        return df

    chunks = df.progress_apply(apply_chunking, axis=1)

    # concat and explode to get one row per chunk
    exploded = (
        pd.concat([df.reset_index(drop=True), chunks.reset_index(drop=True)], axis=1)
        .explode(["chunk_index", "chunk_text"])
        .reset_index(drop=True)
    )

    # drop rows with empty chunk_text
    exploded = exploded[exploded["chunk_text"].notna() & (exploded["chunk_text"] != "")]
    return exploded
