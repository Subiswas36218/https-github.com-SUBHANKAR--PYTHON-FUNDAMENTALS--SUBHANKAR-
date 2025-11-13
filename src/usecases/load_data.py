import csv
from pathlib import Path
from typing import Dict

from src.models.relational import Author, ScientificArticle
from src.storage.relational_db import Session


def load_data_from_csv(path: Path) -> None:
    print(f"Loading data from: {path}")

    with open(path, "r", encoding="utf-8") as f, Session() as session:
        reader = csv.DictReader(f, delimiter=";", skipinitialspace=True)

        # Cache authors to avoid repeated SELECT queries
        author_cache: Dict[tuple, Author] = {}

        inserted_articles = 0
        skipped_articles = 0

        for row_num, row in enumerate(reader, start=1):
            try:
                arxiv_id = row["arxiv_id"].strip().strip('"')
                title = row["title"].strip().strip('"')
                summary = row["summary"].strip().strip('"')
                file_path = row["file_path"].strip().strip('"')
                author_name = row["author_full_name"].strip().strip('"')
                author_title = row["author_title"].strip().strip('"')

                existing_article = (
                    session.query(ScientificArticle)
                    .filter(ScientificArticle.arxiv_id == arxiv_id)
                    .first()
                )

                if existing_article:
                    print(f"Duplicate article skipped: {arxiv_id}")
                    skipped_articles += 1
                    continue

                author_key = (author_name, author_title)

                if author_key in author_cache:
                    author = author_cache[author_key]
                else:
                    author = (
                        session.query(Author)
                        .filter(Author.full_name == author_name,
                                Author.title == author_title)
                        .first()
                    )
                    if not author:
                        author = Author(full_name=author_name, title=author_title)
                        session.add(author)

                    author_cache[author_key] = author
                article = ScientificArticle(
                    arxiv_id=arxiv_id,
                    title=title,
                    summary=summary,
                    file_path=file_path,
                    author=author
                )

                session.add(article)
                inserted_articles += 1

            except Exception as e:
                print(f"Error in row {row_num}: {e}")
                continue

        session.commit()

        print("\n Load Completed")
        print(f"Articles inserted: {inserted_articles}")
        print(f"Articles skipped (duplicates): {skipped_articles}")
        print(f"Authors in cache: {len(author_cache)}")


if __name__ == "__main__":
    load_data_from_csv(Path("data/articles.csv"))

            