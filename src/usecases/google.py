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
        start = max(end - overlap, end)  # avoid infinite loop if overlap > chunk_size

    return chunks


def embed_article(row: pd.Series) -> pd.Series:
    """
    Take one row with 'md_text' and 'arxiv_id' and return a Series:
      - 'embedding' → list[float] or None
    Handles quota errors (429) gracefully and stops further API calls once quota is hit.
    """
    global _EMBEDDING_DISABLED

    # If we already know quota is exhausted, skip API call
    if _EMBEDDING_DISABLED:
        return pd.Series({"embedding": None}, index=["embedding"])

    arxiv_id = str(row.get("arxiv_id", "") or "")
    md_text = str(row.get("md_text", "") or "").strip()

    if not md_text:
        LOG.warning("embed_article: empty md_text for row %s", arxiv_id or "<no-id>")
        return pd.Series({"embedding": None}, index=["embedding"])

    # Optional: chunk and log some stats (as in your logs)
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
        # You can also pass the chunks and average their embeddings instead of full doc
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[md_text],
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="SEMANTIC_SIMILARITY",
            ),
        )

        # We passed a single content, so expect one embedding
        # embedding = result.embeddings[0].values  # list[float]
        # Optional: convert to np.array if you prefer
        embedding = np.array(result.embeddings[0].values, dtype=float)

        return pd.Series({"embedding": embedding}, index=["embedding"])

    except Exception as exc:  # broad, but we log & handle
        msg = str(exc)
        LOG.error(
            "embed_article: failed to embed row %s: %s", arxiv_id or "<no-id>", msg
        )

        # If it's a quota / rate limit issue, disable further calls in this run
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            LOG.error(
                "embed_article: quota / rate limit hit, "
                "disabling further embedding calls in this run."
            )
            _EMBEDDING_DISABLED = True

    return pd.Series({"embedding": None}, index=["embedding"])


def embed_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply embed_article to each row and append an 'embedding' column.
    """
    embedding_df = df.progress_apply(embed_article, axis=1)
    out = pd.concat(
        [df.reset_index(drop=True), embedding_df.reset_index(drop=True)],
        axis=1,
    )
    print(df.dtypes)

    num_ok = out["embedding"].notna().sum()
    num_total = len(out)
    LOG.info("embed_documents: %d/%d rows have embeddings", num_ok, num_total)

    return out
