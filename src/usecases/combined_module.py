from pathlib import Path

from src.usecases.export_articles import export_from_db
from src.usecases.import_articles import load_data_from_csv
from src.usecases.search_text import search_text_index

if __name__ == "__main__":
    # Load data from CSV into relational database
    csv_path = Path("data/papers/articles.csv")
    load_data_from_csv(csv_path)

    # Export articles from relational database to MongoDB
    export_from_db()

    # Search for articles in MongoDB using text index
    results = search_text_index("galaxies")
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")
