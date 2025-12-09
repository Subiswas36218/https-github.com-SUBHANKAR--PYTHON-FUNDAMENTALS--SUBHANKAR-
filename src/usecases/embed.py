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


def embed_article(row: pd.Series) -> pd.Series:
    """
    Take one row with 'md_text' and 'arxiv_id' and return a Series with:
      - 'chunk_texts'      → list[str]         (subset of chunks used)
      - 'chunk_embeddings' → np.ndarray       (shape [n_chunks, 768])
      - 'embedding'        → list[float] | None  (mean-pooled embedding)
    Handles quota errors (429) gracefully and stops further API calls
    once quota is hit.
    """
    global _EMBEDDING_DISABLED

    if _EMBEDDING_DISABLED:
        return pd.Series(
            {
                "chunk_texts": None,
                "chunk_embeddings": None,
                "embedding": None,
            }
        )

    arxiv_id = str(row.get("arxiv_id", "") or "")
    md_text = str(row.get("md_text", "") or "").strip()

    if not md_text:
        LOG.warning("embed_article: empty md_text for row %s", arxiv_id or "<no-id>")
        return pd.Series(
            {
                "chunk_texts": None,
                "chunk_embeddings": None,
                "embedding": None,
            }
        )

    chunks = _chunk_text(md_text, chunk_size=1000, overlap=200)
    avg_len = sum(len(c) for c in chunks) / max(len(chunks), 1)
    LOG.info(
        "embed_article: %s → %d chunks, avg length %.1f chars",
        arxiv_id or "<no-id>",
        len(chunks),
        avg_len,
    )

    client = get_client()

    try:
        # For now, embed only the first few chunks to stay under limits.
        # You can tune this.
        contents = chunks[:2]

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="SEMANTIC_SIMILARITY",
            ),
        )

        if not getattr(result, "embeddings", None):
            LOG.error(
                "embed_article: no embeddings returned for %s", arxiv_id or "<no-id>"
            )
            return pd.Series(
                {
                    "chunk_texts": contents,
                    "chunk_embeddings": None,
                    "embedding": None,
                }
            )

        chunk_embeddings = np.array(
            [np.array(e.values, dtype=float) for e in result.embeddings], dtype=float
        )

        # Mean-pool chunk embeddings into a single vector for the article.
        pooled: np.ndarray = chunk_embeddings.mean(axis=0)
        embedding_list: list[float] = pooled.tolist()

        return pd.Series(
            {
                "chunk_texts": contents,
                "chunk_embeddings": chunk_embeddings,
                "embedding": embedding_list,
            }
        )

    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        LOG.error(
            "embed_article: failed to embed row %s: %s", arxiv_id or "<no-id>", msg
        )

        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            LOG.error(
                "embed_article: quota / rate limit hit, "
                "disabling further embedding calls in this run.",
            )
            _EMBEDDING_DISABLED = True

        return pd.Series(
            {
                "chunk_texts": None,
                "chunk_embeddings": None,
                "embedding": None,
            }
        )


def embed_documents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply embed_article to each row and append:
      - 'chunk_texts'
      - 'chunk_embeddings'
      - 'embedding'
    """
    embedding_df = df.progress_apply(embed_article, axis=1)
    out = pd.concat(
        [df.reset_index(drop=True), embedding_df.reset_index(drop=True)],
        axis=1,
    )

    if "embedding" in out.columns:
        num_ok = out["embedding"].notna().sum()
        num_total = len(out)
        LOG.info("embed_documents: %d/%d rows have embeddings", num_ok, num_total)
    else:
        LOG.warning("embed_documents: 'embedding' column missing in output")

    return out
