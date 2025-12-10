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


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split long text into overlapping chunks, trying to break at periods."""
    text = text or ""
    start = 0
    chunks: list[str] = []

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        # avoid infinite loop if overlap > chunk_size
        start = max(end - overlap, end)

    return chunks


def _empty_embedding_series() -> pd.Series:
    """Helper: consistent empty result."""
    return pd.Series(
        {
            "embedding": None,
            "chunk_texts": None,
            "chunk_embeddings": None,
        },
        index=["embedding", "chunk_texts", "chunk_embeddings"],
    )


def embed_article(row: pd.Series) -> pd.Series:
    global _EMBEDDING_DISABLED

    if _EMBEDDING_DISABLED:
        return pd.Series(
            {"chunk_texts": None, "embeddings": None},
            index=["chunk_texts", "embeddings"],
        )

    arxiv_id = str(row.get("arxiv_id", "") or "")
    md_text = str(row.get("md_text", "") or "").strip()

    if not md_text:
        LOG.warning("embed_article: empty md_text for row %s", arxiv_id or "<no-id>")
        return pd.Series(
            {"chunk_texts": None, "embeddings": None},
            index=["chunk_texts", "embeddings"],
        )

    chunks = _chunk_text(md_text, chunk_size=1000, overlap=200)
    avg_len = sum(len(c) for c in chunks) / max(len(chunks), 2)
    LOG.info(
        "embed_article: %s → %d chunks, avg length %.1f chars",
        arxiv_id or "<no-id>",
        len(chunks),
        avg_len,
    )

    client = get_client()

    try:
        contents = chunks[:2]
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="SEMANTIC_SIMILARITY",
            ),
        )

        embeddings = np.array(
            [np.array(embedding.values) for embedding in result.embeddings or []],
            dtype=float,
        )

        return pd.Series(
            {"chunk_texts": contents, "embeddings": embeddings},
            index=["chunk_texts", "embeddings"],
        )

    except Exception as exc:
        msg = str(exc)
        LOG.error(
            "embed_article: failed to embed row %s: %s", arxiv_id or "<no-id>", msg
        )

        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            LOG.error(
                "embed_article: quota / rate limit hit, "
                "disabling further embedding calls in this run."
            )
            _EMBEDDING_DISABLED = True

        return pd.Series(
            {"chunk_texts": None, "embeddings": None},
            index=["chunk_texts", "embeddings"],
        )


def embed_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply embed_article to each row and append 'chunk_texts' and 'embeddings' columns.
    """
    embedding_df = df.apply(embed_article, axis=1)
    out = pd.concat(
        [df.reset_index(drop=True), embedding_df.reset_index(drop=True)],
        axis=1,
    )

    num_ok = out["embeddings"].notna().sum()
    num_total = len(out)
    LOG.info("embed_documents: %d/%d rows have embeddings", num_ok, num_total)

    return out
