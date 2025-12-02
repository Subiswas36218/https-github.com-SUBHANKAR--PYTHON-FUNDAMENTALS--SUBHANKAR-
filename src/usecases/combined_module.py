from pathlib import Path

from src.usecases.export_articles import create_in_mongo, download_files
from src.usecases.import_articles import (
    create_in_relational_db,
    load_data_from_xml,
)
from src.usecases.search_text import search_text_index

if __name__ == "__main__":
    # load XML
    df_xml = load_data_from_xml(Path("data/arxiv_articles.xml"))

    # 1) Download remote PDFs into data/papers/, add 'local_file_path' column
    df_with_local = download_files(df_xml)

    # 2) Make sure the DataFrame's 'file_path' column (or local_file_path)
    #    is used by the import pipeline. The import pipeline currently
    #    looks for 'file_path' — ensure it reads the local path.
    #    If create_in_relational_db looks at 'file_path', copy
    #    local_file_path -> file_path.
    df_with_local["file_path"] = df_with_local["local_file_path"].fillna(
        df_with_local["file_path"]
    )

    # 3) Insert into relational DB, then export to Mongo
    df_after_sql = create_in_relational_db(df_with_local)
    df_after_mongo = create_in_mongo(df_after_sql)

    print("DataFrame after relational DB insertion:")
    print(df_after_mongo.to_string(index=False))
    df = (
        load_data_from_xml(Path("data/arxiv_articles.xml"))
        .pipe(create_in_relational_db)
        .pipe(download_files)
        .pipe(create_in_mongo)
    )
    print("DataFrame after relational DB insertion:")
    print(df)
    #
    results = search_text_index("galaxies")
    print("len results:", len(results))
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")

    # data/papers/articles.csv -> load_data_from_csv() ->
    # export_from_db() -> search_text_index() -> print results
