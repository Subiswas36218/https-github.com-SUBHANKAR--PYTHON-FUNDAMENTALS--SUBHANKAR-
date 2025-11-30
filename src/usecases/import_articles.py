from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError  # pyright: ignore[reportMissingImports]

from src.models.relational import Author, ScientificArticle
from src.storage.relational_db import Session

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PDF_DIR = Path("data/papers")


def clean(value: Any) -> str:
    """Normalize CSV cell to a trimmed string (empty string for NaN-like values)."""
    if pd.isna(value):
        return ""
    return str(value).strip().strip('"').strip("'")


def _resolve_pdf_path(raw_file_path: str) -> Path | None:
    if not raw_file_path:
        return None

    if not raw_file_path.lower().endswith(".pdf"):
        return None

    candidates = [
        Path(raw_file_path),
        Path("data/papers") / Path(raw_file_path).name,
        Path("data/papers/articles") / Path(raw_file_path).name,
    ]

    for c in candidates:
        c = c.resolve()
        if c.exists():
            return c

    return None


# Provide the real SQLAlchemy Session *type* to type-checkers only.
if TYPE_CHECKING:
    from sqlalchemy.orm import (
        Session as SA_Session,  # pyright: ignore[reportMissingImports]
    )


def _get_or_create_author(session: SA_Session, full_name: str, title: str) -> Author:
    """
    Return an existing Author with the given full_name if present, otherwise create it.
    Uses the session passed in.
    """
    if not full_name:
        author = Author(full_name=None, title=title or None)
        session.add(author)
        session.flush()
        return author

    stmt = select(Author).where(Author.full_name == full_name)
    existing = session.scalar(stmt)
    if existing:
        return existing

    author = Author(full_name=full_name, title=title or None)
    session.add(author)
    session.flush()
    return author


def save_article(line: dict[str, Any]) -> tuple[int | None, int | None] | None:
    """
    Save a single article (and author) into the relational DB.

    Returns:
      - (article_id, author_id) on success (ints or None)
      - (0, 0) for a duplicate that couldn't be resolved further
      - None if the row was skipped (e.g., missing/invalid PDF)
    """
    arxiv_id = clean(line.get("arxiv_id", ""))
    title = clean(line.get("title", ""))
    summary = clean(line.get("summary", ""))
    author_full_name = clean(line.get("author_full_name", ""))
    author_title = clean(line.get("author_title", ""))
    raw_file_path = clean(line.get("file_path", ""))

    pdf_path = _resolve_pdf_path(raw_file_path)
    if pdf_path is None:
        LOG.warning("SKIPPED malformed row (invalid or missing PDF): %s", raw_file_path)
        return None

    with Session() as session:
        try:
            # Check for an existing article first (avoid duplicate insert attempts)
            existing = (
                session.query(ScientificArticle)
                .filter(ScientificArticle.arxiv_id == arxiv_id)
                .one_or_none()
            )
            if existing:
                LOG.info(
                    "Found existing article, skipping insert: %s (id=%s)",
                    arxiv_id,
                    existing.id,
                )
                return int(existing.id), int(
                    existing.author_id
                ) if existing.author_id is not None else None

            # Create or get the author
            author = _get_or_create_author(session, author_full_name, author_title)

            # Create and persist the article
            article = ScientificArticle(
                title=title or None,
                summary=summary or None,
                file_path=str(pdf_path),
                arxiv_id=arxiv_id or None,
                author_id=author.id,
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            LOG.info("Inserted: %s (db id=%s)", arxiv_id, article.id)
            return int(article.id), int(author.id)

        except IntegrityError:
            # Race or duplicate detected: rollback and try to fetch existing record
            session.rollback()
            existing = (
                session.query(ScientificArticle)
                .filter(ScientificArticle.arxiv_id == arxiv_id)
                .one_or_none()
            )
            if existing:
                LOG.info(
                    "IntegrityError but found existing article: %s (id=%s)",
                    arxiv_id,
                    existing.id,
                )
                return int(existing.id), int(
                    existing.author_id
                ) if existing.author_id is not None else None

            LOG.warning("Skipped duplicate (unknown id): %s", arxiv_id)
            return 0, 0

        except Exception as exc:
            session.rollback()
            LOG.exception("Unexpected error while saving article %s: %s", arxiv_id, exc)
            return None


def load_data_from_csv(path: Path) -> pd.DataFrame:
    """
    Read CSV into DataFrame. Matches original separators/quotechar.
    """
    return pd.read_csv(
        path,
        sep=";",
        quotechar="'",
        skipinitialspace=True,
        encoding="utf-8",
    )


def create_in_relational_db(df: pd.DataFrame) -> pd.DataFrame:
    ids = df.apply(save_article, axis=1)
    df = pd.concat([df, ids], axis=1)
    """
    Persist rows from the DataFrame into the relational DB.

    Returns a copy of the DataFrame with added 'db_id' and 'author_id' columns
    containing the created article primary key and the article.author_id
    (or <NA> if skipped).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("create_in_relational_db expects a pandas.DataFrame")

    db_ids: list[int | None] = []
    author_ids: list[int | None] = []

    rows = df.to_dict(orient="records")

    for i, line in enumerate(rows):
        LOG.debug("Processing row %d arxiv_id=%s", i, line.get("arxiv_id"))
        result = save_article(line)

        if result is None:
            # skipped (invalid PDF or fatal error)
            db_ids.append(None)
            author_ids.append(None)
            continue

        # result is a tuple (db_id, author_id) or (0,0)
        db_id_val, author_id_val = result
        # Normalize 0 → None (if you prefer to keep 0, remove these lines)
        if db_id_val == 0:
            db_id_val = None
        if author_id_val == 0:
            author_id_val = None

        db_ids.append(db_id_val)
        author_ids.append(author_id_val)

    out_df = df.copy()
    out_df["db_id"] = pd.Series(db_ids, index=out_df.index, dtype="Int64")
    out_df["author_id"] = pd.Series(author_ids, index=out_df.index, dtype="Int64")

    LOG.info("Relational ingest complete. DataFrame rows: %d", len(out_df))
    return out_df
