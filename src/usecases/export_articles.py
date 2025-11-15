from src.storage.mongo import connect  # noqa: F401

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"
connect(db="PythonDE", host=MONGO_URL, alias="default")

from sqlalchemy import select
from src.models.relational import ScientificArticle
from src.models.mongo import ScientificArticle as MongoArticle, Author as MongoAuthor
from src.storage.relational_db import Session


def export_from_db():
    with Session() as session:
        query = select(ScientificArticle)
        result = session.execute(query)

        for article in result.scalars():
            m_author = MongoAuthor(
                db_id=article.author.id,
                full_name=article.author.full_name,
                title=article.author.title
            )

            m_article = MongoArticle(
                db_id=article.id,
                title=article.title,
                summary=article.summary,
                file_path=article.file_path,
                created_at=article.created_at,
                arxiv_id=article.arxiv_id,
                author=m_author
            )

            m_article.save()
            print(f"Exported → MongoDB: {article.arxiv_id}")


if __name__ == "__main__":
    export_from_db()

                   
            
