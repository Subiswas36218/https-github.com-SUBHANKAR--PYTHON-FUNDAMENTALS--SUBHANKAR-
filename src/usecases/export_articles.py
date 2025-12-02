import logging
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import pandas as pd
import pymupdf4llm  # pyright: ignore[reportMissingImports]
import requests  # pyright: ignore[reportMissingImports]

import src.storage.mongo  # noqa: F401 (ensure DB connection)
from src.models.mongo import Author as MongoAuthor  # mongoengine EmbeddedDocument
from src.models.mongo import ScientificArticle as MongoArticle  # mongoengine Document

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PAPERS_DIR = Path("data/papers")
PAPERS_DIR.mkdir(parents=True, exist_ok=True)


def extract_markdown(file_path: str, arxiv_id: str) -> str | None:
    """Return markdown text for a local PDF path, or None on failure."""
    try:
        p = Path(file_path)
        if not p.exists():
            LOG.warning(
                "extract_markdown: file not found for %s -> %s", arxiv_id, file_path
            )
            return None
        md = pymupdf4llm.to_markdown(str(p))
        return cast(str | None, md)
    except Exception as exc:
        LOG.exception("FILE ERROR for %s: %s", arxiv_id or "<no-id>", exc)
        return None


def _get_field(row: Any, field: str) -> Any:
    """Universal accessor for Series, dict, record, or object."""
    if isinstance(row, dict):
        return row.get(field, None)
    if hasattr(row, "get"):
        try:
            return row.get(field, None)
        except Exception:
            pass
    if hasattr(row, field):
        try:
            return getattr(row, field)
        except Exception:
            pass
    try:
        return row[field]
    except Exception:
        return None


def _is_present(value: Any) -> bool:
    """
    Return True if value is valid and non-empty.
    Handles pd.NA, NaN, and empty strings.
    """

    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except Exception:
        pass
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def download_file(row: pd.Series) -> str:
    """
    Given a row (Series or dict), return a local file path (string).
    If download fails or no file found, returns an empty string.
    """
    raw = _get_field(row, "file_path") or ""
    raw = str(raw).strip()
    if not raw:
        return ""

    if raw.startswith("data/file/"):
        raw = raw[len("data/file/") :]

    parsed = urlparse(raw)

    if parsed.scheme in ("http", "https"):
        filename = Path(parsed.path).name
        if not filename:
            LOG.warning("download_file: no filename in URL %s", raw)
            return ""

        local_path = PAPERS_DIR / filename

        if local_path.exists():
            return str(local_path)

        try:
            with requests.get(raw, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            LOG.info("Downloaded: %s -> %s", raw, local_path)
            return str(local_path)
        except Exception as exc:
            LOG.exception("Download failed for %s: %s", raw, exc)
            try:
                if local_path.exists():
                    local_path.unlink(missing_ok=True)
            except Exception:
                pass
            return ""

    local_candidate = Path(raw)
    if not local_candidate.is_absolute():
        candidate = PAPERS_DIR / local_candidate.name
    else:
        candidate = local_candidate

    if candidate.exists():
        return str(candidate.resolve())

    LOG.debug("Local file not found for %s; returning raw path", raw)
    return raw


def save_article(row: pd.Series) -> Any:
    """
    Insert or update a MongoArticle from the given row.
    Returns:
      - MongoArticle document (on success), or
      - string id for documents without an arxiv_id, or
      - empty string on failure.
    """
    try:
        arxiv_raw = _get_field(row, "arxiv_id")
        arxiv_id = str(arxiv_raw).strip() if _is_present(arxiv_raw) else None

        title_raw = _get_field(row, "title")
        title = str(title_raw).strip() if _is_present(title_raw) else ""

        summary_raw = _get_field(row, "summary")
        summary = str(summary_raw).strip() if _is_present(summary_raw) else ""

        file_path_raw = _get_field(row, "file_path")
        file_path = str(file_path_raw).strip() if _is_present(file_path_raw) else ""

        # Prefer 'local_file_path' but guard against pd.NA
        local_raw = _get_field(row, "local_file_path")
        if not _is_present(local_raw):
            local_raw = _get_field(row, "local_file")
        local_file_path = str(local_raw).strip() if _is_present(local_raw) else ""

        author_full_name_raw = _get_field(row, "author_full_name")
        author_full_name = (
            str(author_full_name_raw).strip()
            if _is_present(author_full_name_raw)
            else ""
        )

        author_title_raw = _get_field(row, "author_title")
        author_title = (
            str(author_title_raw).strip() if _is_present(author_title_raw) else ""
        )

        author_db_id_raw = _get_field(row, "db_id")
        if not _is_present(author_db_id_raw):
            author_db_id_raw = _get_field(row, "author_db_id")

        try:
            author_db_id = int(author_db_id_raw) if _is_present(author_db_id_raw) else 0
        except Exception:
            author_db_id = 0

        m_author = MongoAuthor(
            db_id=author_db_id or 0, full_name=author_full_name, title=author_title
        )

        md_text: str | None = None
        if _is_present(local_file_path):
            md_text = extract_markdown(local_file_path, arxiv_id or "")
        elif _is_present(file_path) and not urlparse(file_path).scheme:
            md_text = extract_markdown(file_path, arxiv_id or "")

        doc_kwargs: dict[str, Any] = dict(
            db_id=author_db_id or 0,
            title=title,
            summary=summary,
            file_path=(local_file_path or file_path or ""),
            arxiv_id=(arxiv_id or ""),
            author=m_author,
            text=md_text,
        )

        if _is_present(arxiv_id):
            existing = MongoArticle.objects(arxiv_id=arxiv_id).first()
            if existing:
                for k, v in doc_kwargs.items():
                    if k == "author":
                        existing.author = v
                    else:
                        setattr(existing, k, v)
                existing.save()
                LOG.info("Updated → %s", arxiv_id)
                return existing

            new_doc = MongoArticle(**doc_kwargs)
            new_doc.save()
            LOG.info("Inserted → %s", arxiv_id)
            return new_doc

        new_doc = MongoArticle(**doc_kwargs)
        new_doc.save()
        LOG.info("Inserted (no arxiv_id) → %s", new_doc.id)
        return str(new_doc.id)

    except Exception as exc:
        LOG.exception("Failure saving article: %s", exc)
        return ""


def download_files(df: pd.DataFrame) -> pd.DataFrame:
    """
    Download remote files and return a new DataFrame with a 'local_file_path' column.
    """
    local_paths = df.apply(download_file, axis=1)
    out = df.copy()
    out["local_file_path"] = pd.Series(local_paths, index=out.index, dtype="string")
    return out


def create_in_mongo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Save rows into MongoDB and add a 'mongo_id' column containing the Mongo ID (string).
    """
    results = df.apply(save_article, axis=1)

    mongo_ids = []
    for r in results.tolist():
        if hasattr(r, "id"):
            mongo_ids.append(str(r.id))
        elif isinstance(r, str) and r:
            mongo_ids.append(r)
        else:
            mongo_ids.append("")

    out = df.copy()
    out["mongo_id"] = pd.Series(mongo_ids, index=out.index, dtype="string")
    return out
