from pathlib import Path

from tqdm.auto import tqdm

from src.usecases.arxiv import fetch_arxiv_articles
from src.usecases.embed import embed_documents
from src.usecases.export_articles import (
    convert_to_markdown,
    create_in_mongo,
    download_files,
)
from src.usecases.import_articles import (
    create_in_relational_db,
    load_data_from_xml,
)
from src.usecases.search_text import search_text_index

tqdm.pandas(desc="Loading articles")


if __name__ == "__main__":
    df_xml = load_data_from_xml(Path("data/arxiv_articles.xml"))

    df_with_local = download_files(df_xml)
    df_with_local["file_path"] = df_with_local["local_file_path"].fillna(
        df_with_local["file_path"]
    )

    df_after_sql = create_in_relational_db(df_with_local)
    df_after_mongo = create_in_mongo(df_after_sql)

    print("DataFrame after relational DB insertion:")
    print(df_after_mongo.to_string(index=False))

    df = (
        fetch_arxiv_articles("proton")
        # load_data_from_xml(Path("data/papers/arxiv_articles_cut.xml"))
        .pipe(create_in_relational_db)
        .pipe(download_files)
        .pipe(convert_to_markdown)
        .pipe(embed_documents)
        .pipe(create_in_mongo)
    )

    print("DataFrame after markdown + embeddings:")
    print(df)

    results = search_text_index("angular")
    print("len results:", len(results))
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")

    # data/papers/articles.csv -> load_data_from_csv() ->
    # export_from_db() -> search_text_index() -> print results
