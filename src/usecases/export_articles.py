import src.storage.mongo  # noqa
import pymupdf4llm # pyright: ignore[reportMissingImports]

from sqlalchemy import select # pyright: ignore[reportMissingImports]
from mongoengine.errors import DoesNotExist # pyright: ignore[reportMissingImports]

from src.models.relational import ScientificArticle
from src.models.mongo import ScientificArticle as MongoArticle, Author as MongoAuthor
from src.storage.relational_db import Session


def export_from_db() -> None:
    with Session() as session:
        result = session.execute(select(ScientificArticle))

        for article in result.scalars().all():

            
            m_author = MongoAuthor(
                db_id=article.author.id,
                full_name=article.author.full_name,
                title=article.author.title,
            )

            
            def extract_markdown(path: str) -> str | None:
                try:
                    return pymupdf4llm.to_markdown(path)
                except Exception as e:
                    print(f"FILE ERROR for {article.arxiv_id}: {e}")
                    return None
            try:
                # Try to find existing Mongo record
                m_article = MongoArticle.objects.get(arxiv_id=article.arxiv_id)

                # Reuse existing text OR extract it now if missing
                md_text = m_article.text or extract_markdown(article.file_path)

                # Update the existing record
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
                continue  # ⬅️ VERY IMPORTANT — prevents INSERT block from running

            except DoesNotExist:
                # No existing record → extract markdown (once)
                md_text = extract_markdown(article.file_path)

                # Create new Mongo article
                m_article = MongoArticle(
                    db_id=article.id,
                    title=article.title,
                    summary=article.summary,
                    file_path=article.file_path,
                    created_at=article.created_at,
                    arxiv_id=article.arxiv_id,
                    author=m_author,
                    text=md_text,
                )

                m_article.save()
                print(f"Inserted → {article.arxiv_id}")


if __name__ == "__main__":
    export_from_db()






                   
            
