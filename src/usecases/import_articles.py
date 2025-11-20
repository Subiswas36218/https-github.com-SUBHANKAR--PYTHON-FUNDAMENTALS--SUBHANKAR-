import csv
from pathlib import Path

from sqlalchemy.exc import IntegrityError  # pyright: ignore[reportMissingImports]

from src.models.relational import Author, ScientificArticle
from src.storage.relational_db import Session


# All PDFs are expected to live here
PDF_DIR = Path("data/papers")


def clean(s: str) -> str:
    """Remove spaces and surrounding quotes."""
    return s.strip().strip('"').strip("'")


def load_data_from_csv(path: Path) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for line in reader:
            arxiv_id = clean(line["arxiv_id"])
            title = clean(line["title"])
            summary = clean(line["summary"])
            author_full_name = clean(line["author_full_name"])
            author_title = clean(line["author_title"])

            # ---- Safe file_path handling ----
            raw_file_path = clean(line["file_path"])

            # Skip malformed rows where file_path is not a PDF
            if not raw_file_path.lower().endswith(".pdf"):
                print(f"SKIPPED malformed row (invalid file_path): {raw_file_path}")
                continue

            # Only use filename, ignore any wrong directory in CSV
            filename = Path(raw_file_path).name
            pdf_path = PDF_DIR / filename

            if not pdf_path.exists():
                print(f"WARNING: PDF does not exist → {pdf_path}")
                continue

            with Session() as session:
                try:
                    # Insert author
                    author = Author(
                        full_name=author_full_name,
                        title=author_title,
                    )
                    session.add(author)
                    session.flush()

                    # Insert article
                    article = ScientificArticle(
                        title=title,
                        summary=summary,
                        file_path=str(pdf_path),
                        arxiv_id=arxiv_id,
                        author_id=author.id,
                    )
                    session.add(article)
                    session.commit()

                    print(f"Inserted: {arxiv_id}")

                except IntegrityError:
                    session.rollback()
                    print(f"Skipped duplicate: {arxiv_id}")


if __name__ == "__main__":
    load_data_from_csv(Path("data/papers/articles.csv"))
