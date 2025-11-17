from typing import cast

import pymupdf4llm  # pyright: ignore[reportMissingImports]
from mongoengine.errors import DoesNotExist  # pyright: ignore[reportMissingImports]
from sqlalchemy import select  # pyright: ignore[reportMissingImports]

import src.storage.mongo  # noqa: F401
from src.models.mongo import Author as MongoAuthor
from src.models.mongo import ScientificArticle as MongoArticle
from src.models.relational import ScientificArticle
from src.storage.relational_db import Session


def extract_markdown(file_path: str, arxiv_id: str) -> str | None:
    """
    Convert PDF to markdown. Returns:
    - str: Extracted markdown
    - None: On failure
    """
    try:
        # pymupdf4llm returns Any → cast to str for mypy
        return cast(str, pymupdf4llm.to_markdown(file_path))
    except Exception as exc:  # noqa: BLE001
        print(f"FILE ERROR for {arxiv_id}: {exc}")
        return None


def export_from_db() -> None:
    """Export all SQL ScientificArticle rows into MongoDB."""
    with Session() as session:
        result = session.execute(select(ScientificArticle))

        for article in result.scalars().all():
            # Build Mongo Author object
            m_author = MongoAuthor(
                db_id=article.author.id,
                full_name=article.author.full_name,
                title=article.author.title,
            )

            try:
                # Try to find an existing Mongo document
                m_article = MongoArticle.objects.get(arxiv_id=article.arxiv_id)

                md_text = (
                    m_article.text
                    if m_article.text
                    else extract_markdown(article.file_path, article.arxiv_id)
                )

                # Update the existing Mongo document
                m_article.update(
                    set__db_id=article.id,
                    set__title=article.title,
                    set__summary=article.summary,
                    set__file_path=article.file_path,
                    set__created_at=article.created_at,
                    set__arxiv_id=article.arxiv_id,
                    set__author=m_author,
                    set__text=md_text,
                )

                print(f"Updated → {article.arxiv_id}")
                continue

            except DoesNotExist:
                # Document does not exist → create new one
                md_text = extract_markdown(article.file_path, article.arxiv_id)

                new_doc = MongoArticle(
                    db_id=article.id,
                    title=article.title,
                    summary=article.summary,
                    file_path=article.file_path,
                    created_at=article.created_at,
                    arxiv_id=article.arxiv_id,
                    author=m_author,
                    text=md_text,
                )

                new_doc.save()
                print(f"Inserted → {article.arxiv_id}")


if __name__ == "__main__":
    export_from_db()
