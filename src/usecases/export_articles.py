from typing import Any, cast

import pandas as pd
import pymupdf4llm  # pyright: ignore[reportMissingImports]
from mongoengine.errors import DoesNotExist  # pyright: ignore[reportMissingImports]

import src.storage.mongo  # noqa: F401
from src.models.mongo import Author as MongoAuthor
from src.models.mongo import ScientificArticle as MongoArticle


def extract_markdown(file_path: str, arxiv_id: str) -> str | None:
    try:
        return cast(str, pymupdf4llm.to_markdown(file_path))
    except Exception as exc:
        print(f"FILE ERROR for {arxiv_id}: {exc}")
        return None


def _get_field(row: Any, field: str) -> Any:
    """
    Robust accessor - works for pandas.Series, numpy.record, dict or object.
    Returns None if not found.
    """
    # dict-like first
    try:
        if isinstance(row, dict):
            return row.get(field, None)
    except Exception:
        pass

    # pandas Series or mapping-like
    try:
        if hasattr(row, "get"):
            val = row.get(field, None)
            if val is not None:
                return val
    except Exception:
        pass

    # attribute access (numpy.record exposes attributes)
    try:
        if hasattr(row, field):
            return getattr(row, field)
    except Exception:
        pass

    # indexing by name (numpy.recarray)
    try:
        return row[field]
    except Exception:
        return None


def _is_present(value: Any) -> bool:
    """
    Return True if value is present (not None, not pd.NA, not empty string).
    Use this instead of 'if value:' which is ambiguous with pd.NA.
    """
    if value is None:
        return False
    # pandas special NA
    try:
        if pd.isna(value):
            return False
    except Exception:
        pass
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def save_article(row: pd.Series) -> Any:
    """
    Upsert one article into MongoDB. Returns the MongoArticle instance or a
    string id, or an empty string on failure — kept intentionally
    consistent with previous pipeline.
    """
    try:
        # read fields in a robust way
        arxiv_id_raw = _get_field(row, "arxiv_id")
        arxiv_id = str(arxiv_id_raw).strip() if _is_present(arxiv_id_raw) else None

        title_raw = _get_field(row, "title")
        title = str(title_raw).strip() if _is_present(title_raw) else ""

        summary_raw = _get_field(row, "summary")
        summary = str(summary_raw).strip() if _is_present(summary_raw) else ""

        file_path_raw = _get_field(row, "file_path")
        file_path = str(file_path_raw).strip() if _is_present(file_path_raw) else None

        # author fields: support both db_id and author_db_id names
        author_db_id_raw = _get_field(row, "db_id") or _get_field(row, "author_db_id")
        try:
            author_db_id = (
                int(author_db_id_raw) if _is_present(author_db_id_raw) else None
            )
        except Exception:
            author_db_id = None

        author_full_name_raw = _get_field(row, "author_full_name") or _get_field(
            row, "author"
        )
        author_full_name = (
            str(author_full_name_raw).strip()
            if _is_present(author_full_name_raw)
            else ""
        )

        author_title_raw = _get_field(row, "author_title")
        author_title = (
            str(author_title_raw).strip() if _is_present(author_title_raw) else ""
        )

        # Build Mongo embedded author
        m_author = MongoAuthor(
            db_id=author_db_id or 0,
            full_name=author_full_name,
            title=author_title,
        )

        md_text = None
        if _is_present(file_path):
            # mypy can't infer that file_path is a str here; make it explicit
            md_text = extract_markdown(cast(str, file_path), arxiv_id or "")

        # Prepare kwargs: put None or empty string values as appropriate to
        # match your Mongo schema.
        kwargs = dict(
            db_id=author_db_id or 0,
            title=title,
            summary=summary,
            file_path=file_path or "",
            arxiv_id=arxiv_id or "",
            author=m_author,
            text=md_text,
        )

        # Upsert: try to find existing by arxiv_id when available
        if _is_present(arxiv_id):
            try:
                m_article = MongoArticle.objects.get(arxiv_id=arxiv_id)
                # update -- use .modify or .update; using update with kwargs as before
                m_article.update(**kwargs)
                # re-fetch updated document so we can return a Document instance
                m_article = MongoArticle.objects.get(arxiv_id=arxiv_id)
                print(f"Updated → {arxiv_id}")
                return m_article
            except DoesNotExist:
                m_article = MongoArticle(**kwargs)
                m_article.save()
                print(f"Inserted → {arxiv_id}")
                return m_article
        else:
            # no arxiv_id: create a document but warn
            m_article = MongoArticle(**kwargs)
            m_article.save()
            print(f"Inserted (no arxiv_id) → {m_article.id}")
            return pd.Series([m_article.id], index=["mongo_id"])

    except Exception as e:
        # keep consistent "Failure: ..." log so your pipeline grep still works
        print(f"Failure: {e}")
        return pd.Series([""], index=["mongo_id"])


def create_in_mongo(df: pd.DataFrame) -> pd.DataFrame:
    # apply save_article to each row and collect results
    ids_series = df.apply(save_article, axis=1)

    # convert the returned values to string IDs (if possible) or None
    mongo_ids: list[str | None] = []
    for val in ids_series.tolist():
        if val is None:
            mongo_ids.append(None)
            continue
        # Document instance (mongoengine) exposes .id.
        # Keep original instance if you prefer.

        if hasattr(val, "id"):
            try:
                mongo_ids.append(str(val.id))
                continue
            except Exception:
                pass
        # maybe already a string id
        if isinstance(val, str) and val != "":
            mongo_ids.append(val)
            continue
        # empty string or unknown → treat as None
        mongo_ids.append(None)

    out = df.copy()
    out["mongo_id"] = pd.Series(mongo_ids, index=out.index, dtype="string")
    return out
