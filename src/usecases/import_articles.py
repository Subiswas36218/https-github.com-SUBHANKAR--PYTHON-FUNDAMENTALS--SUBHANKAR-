import csv
from pathlib import Path

from sqlalchemy.exc import IntegrityError  # pyright: ignore[reportMissingImports]

from src.models.relational import Author, ScientificArticle
from src.storage.relational_db import Session


def clean(s: str) -> str:
    """Remove spaces and surrounding quotes."""
    return s.strip().strip('"').strip("'")


def load_data_from_csv(path: Path) -> None:
    with open(path) as f:
        reader = csv.DictReader(f, delimiter=";")

        for line in reader:
            # Clean the fields from the CSV
            arxiv_id = clean(line["arxiv_id"])
            title = clean(line["title"])
            summary = clean(line["summary"])
            file_path = clean(line["file_path"])
            author_full_name = clean(line["author_full_name"])
            author_title = clean(line["author_title"])

            # Verify PDF exists
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                print(f"WARNING: PDF does not exist → {file_path}")

                continue

            with Session() as session:
                try:
                    author = Author(
                        full_name=author_full_name,
                        title=author_title,
                    )
                    session.add(author)
                    session.flush()

                    article = ScientificArticle(
                        title=title,
                        summary=summary,
                        file_path=str(pdf_path),
                        arxiv_id=arxiv_id,
                        author_id=author.id,
                    )
                    session.add(article)
                    session.commit()

                    print(f"Success: {arxiv_id}")

                except IntegrityError as e:
                    print(f"Failure for {arxiv_id}: {e}")


if __name__ == "__main__":
    load_data_from_csv(Path("data/articles.csv"))
