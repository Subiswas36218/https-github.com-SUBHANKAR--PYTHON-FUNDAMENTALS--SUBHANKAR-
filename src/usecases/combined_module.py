from pathlib import Path

from src.usecases.export_articles import create_in_mongo
from src.usecases.import_articles import create_in_relational_db, load_data_from_csv
from src.usecases.search_text import search_text_index

if __name__ == "__main__":
    # Load data from CSV into relational DB
    df = (
        load_data_from_csv(Path("data/papers/articles.csv"))
        .pipe(create_in_relational_db)
        .pipe(create_in_mongo)
    )
    print("DataFrame after relational DB insertion:")
    print(df)

    results = search_text_index("galaxies")
    print("len results:", len(results))
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")

        # data/papers/articles.csv -> load_data_from_csv() ->
        # export_from_db() -> search_text_index() -> print results
