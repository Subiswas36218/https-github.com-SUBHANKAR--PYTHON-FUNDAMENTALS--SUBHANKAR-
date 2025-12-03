from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pandas as pd
from lxml import etree
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


def _resolve_pdf_path(raw_file_path: str | None) -> Path | None:
    """
    Attempt to resolve and return an existing Path for the given raw_file_path.
    This function is tolerant of paths that omit the '.pdf' suffix and will
    test several candidate locations (local and legacy folders).
    Returns None if path is invalid or the file does not exist.
    """
    if not raw_file_path:
        return None

    raw = str(raw_file_path).strip()
    # accept both forms: with .pdf or without
    candidates = []

    # direct user-provided path (as-is)
    candidates.append(Path(raw))

    # if not already ending with .pdf, consider adding it
    if not raw.lower().endswith(".pdf"):
        candidates.append(Path(raw + ".pdf"))

    # try placing the name under the known papers dir
    candidates.append(PDF_DIR / Path(raw).name)
    if not Path(raw).name.lower().endswith(".pdf"):
        candidates.append(PDF_DIR / (Path(raw).name + ".pdf"))

    # legacy folder
    candidates.append(Path("data/papers/articles") / Path(raw).name)
    if not Path(raw).name.lower().endswith(".pdf"):
        candidates.append(Path("data/papers/articles") / (Path(raw).name + ".pdf"))

    # resolve and test existence
    for c in candidates:
        try:
            resolved = c.resolve()
        except Exception:
            resolved = c
        if resolved.exists():
            return resolved

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
    fullname_val = full_name or None
    title_val = title or None

    if fullname_val is None:
        author = Author(full_name=None, title=title_val)
        session.add(author)
        session.flush()
        return author

    stmt = select(Author).where(Author.full_name == fullname_val)
    existing = session.scalar(stmt)
    if existing:
        return existing

    author = Author(full_name=fullname_val, title=title_val)
    session.add(author)
    session.flush()
    return author


def save_article(line: dict[str, Any]) -> tuple[int | None, int | None] | None:
    """
    Save a single article (and author) into the relational DB.

    Returns:
      - (article_id, author_id) on success (ints or None)
      - None if the row was skipped (e.g., missing/invalid PDF or fatal error)
    """
    arxiv_id_raw = clean(line.get("arxiv_id", ""))
    arxiv_id = arxiv_id_raw or None
    title = clean(line.get("title", "")) or None
    summary = clean(line.get("summary", "")) or None
    author_full_name = clean(line.get("author_full_name", "")) or None
    author_title = clean(line.get("author_title", "")) or None
    raw_file_path = clean(line.get("file_path", ""))

    pdf_path = _resolve_pdf_path(raw_file_path)
    if pdf_path is None:
        LOG.warning("SKIPPED malformed row (invalid or missing PDF): %s", raw_file_path)
        return None

    with Session() as session:
        try:
            if arxiv_id is not None:
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

            author = _get_or_create_author(
                session, author_full_name or "", author_title or ""
            )

            article = ScientificArticle(
                title=title or "",
                summary=(summary[:500] if summary else None),
                file_path=str(pdf_path),
                arxiv_id=arxiv_id,
                author_id=author.id,
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            LOG.info("Inserted: %s (db id=%s)", arxiv_id or "<no-arxiv-id>", article.id)
            return int(article.id), int(author.id)

        except IntegrityError:
            session.rollback()
            if arxiv_id is not None:
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

            LOG.warning(
                "Skipped duplicate or integrity error for row with arxiv_id=%s",
                arxiv_id,
            )
            return None

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


def load_data_from_xml(path: Path) -> pd.DataFrame:
    """
    Parse an Atom XML file and return a DataFrame with columns:
      arxiv_id, title, summary, file_path, author_full_name, author_title
    Robust to missing elements and preserves order.
    """
    ATOM = "{http://www.w3.org/2005/Atom}"
    records: list[dict[str, str | None]] = []

    raw = Path(path).read_bytes()
    root = etree.fromstring(raw)

    for entry in root.findall(f".//{ATOM}entry"):
        rec: dict[str, str | None] = {
            "arxiv_id": None,
            "title": None,
            "summary": None,
            "file_path": None,
            "author_full_name": None,
            "author_title": None,
        }

        id_el = entry.find(f"{ATOM}id")
        if id_el is not None and id_el.text:
            rec["arxiv_id"] = id_el.text.strip()

        title_el = entry.find(f"{ATOM}title")
        if title_el is not None and title_el.text:
            rec["title"] = title_el.text.strip()

        summary_el = entry.find(f"{ATOM}summary")
        if summary_el is not None and summary_el.text:
            rec["summary"] = summary_el.text.strip()

        pdf_link = None
        for link in entry.findall(f"{ATOM}link"):
            title_attr = link.attrib.get("title", "")
            rel = link.attrib.get("rel", "")
            href = link.attrib.get("href", "")
            if title_attr.lower() == "pdf" or (
                rel
                and rel.lower() == "related"
                and href
                and href.lower().endswith(".pdf")
            ):
                pdf_link = href
                break
        rec["file_path"] = pdf_link.strip() if pdf_link else ""

        authors = entry.findall(f"{ATOM}author")
        if authors:
            first = authors[0]
            name_el = first.find(f"{ATOM}name")
            if name_el is not None and name_el.text:
                rec["author_full_name"] = name_el.text.strip()
            else:
                rec["author_full_name"] = "Unknown"
            rec["author_title"] = "PhD"
        else:
            rec["author_full_name"] = "Unknown"
            rec["author_title"] = "Unknown"

        records.append(rec)

    df = pd.DataFrame.from_records(
        records,
        columns=[
            "arxiv_id",
            "title",
            "summary",
            "file_path",
            "author_full_name",
            "author_title",
        ],
    )

    def map_href_to_local(href: str | None) -> str:
        if not href:
            return ""
        try:
            p = Path(href)
            return str(Path("data/file") / p.name)
        except Exception:
            return href

    df["file_path"] = df["file_path"].apply(map_href_to_local)

    # Normalize string-like columns to avoid pd.NA truthiness elsewhere
    for c in [
        "arxiv_id",
        "title",
        "summary",
        "file_path",
        "author_full_name",
        "author_title",
    ]:
        if c in df.columns:
            df[c] = df[c].astype("string").fillna("").astype(str)

    return df


def load_data_from_raw_xml(path: Path) -> pd.DataFrame:
    """
    Legacy/raw XML parser kept for compatibility; uses lxml.etree directly.
    """
    ATOM = "{http://www.w3.org/2005/Atom}"

    data_dict: dict[str, list[str]] = {
        "arxiv_id": [],
        "title": [],
        "summary": [],
        "author_full_name": [],
        "author_title": [],
        "file_path": [],
    }

    with open(path, "rb") as f:
        data = etree.fromstring(f.read())

        for entry in data.findall(f".//{ATOM}entry"):
            id_el = entry.find(f"{ATOM}id")
            data_dict["arxiv_id"].append(
                id_el.text.strip() if id_el is not None and id_el.text else ""
            )

            title_el = entry.find(f"{ATOM}title")
            data_dict["title"].append(
                title_el.text.strip() if title_el is not None and title_el.text else ""
            )

            summary_el = entry.find(f"{ATOM}summary")
            data_dict["summary"].append(
                summary_el.text.strip()
                if summary_el is not None and summary_el.text
                else ""
            )

            pdf_link = entry.find(f"{ATOM}link[@title='pdf']")
            pdf_url = pdf_link.attrib.get("href") if pdf_link is not None else ""
            data_dict["file_path"].append(f"data/file/{pdf_url}" if pdf_url else "")

            authors = entry.findall(f"{ATOM}author")
            if authors:
                author = authors[0]
                name_el = author.find(f"{ATOM}name")
                name = (
                    name_el.text.strip()
                    if name_el is not None and name_el.text
                    else "Unknown"
                )
                data_dict["author_full_name"].append(name)
                data_dict["author_title"].append("Professor")
            else:
                data_dict["author_full_name"].append("Unknown")
                data_dict["author_title"].append("Unknown")

    return pd.DataFrame(data_dict)


def create_in_relational_db(df: pd.DataFrame) -> pd.DataFrame:
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

    rows = cast(list[dict[str, Any]], df.to_dict(orient="records"))
    for i, line in enumerate(rows):
        LOG.debug("Processing row %d arxiv_id=%s", i, line.get("arxiv_id"))
        result = save_article(line)

        if result is None:
            db_ids.append(None)
            author_ids.append(None)
            continue

        db_id_val, author_id_val = result
        db_ids.append(db_id_val)
        author_ids.append(author_id_val)

    out_df = df.copy()
    out_df["db_id"] = pd.Series(db_ids, index=out_df.index, dtype="Int64")
    out_df["author_id"] = pd.Series(author_ids, index=out_df.index, dtype="Int64")

    LOG.info("Relational ingest complete. DataFrame rows: %d", len(out_df))
    return out_df
