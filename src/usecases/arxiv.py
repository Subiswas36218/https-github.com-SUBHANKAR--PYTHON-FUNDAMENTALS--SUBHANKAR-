from __future__ import annotations

import io

import pandas as pd
import requests

URL = "http://export.arxiv.org/api/query"


def fetch_arxiv_articles(query: str, i: int = 0) -> pd.DataFrame:
    """
    Fetch a small set of arXiv Atom entries and save them to
    data/arxiv_articles.xml. Returns the raw XML text.

    Args:
        query: the arXiv search query (defaults to "electron")
        start: start offset
        max_results: number of results to fetch

    Returns:
        The Atom XML payload as a string.
    """
    # Use string values for params so mypy and requests are happy
    params: dict[str, str | int] = {
        "search_query": f"all:{query}",
        "start": i,
        "max_results": 10,
    }

    resp = requests.get(URL, params=params, timeout=10)
    resp.raise_for_status()

    xml_data = resp.text

    # Ensure output directory exists (simple path write)
    out_path = "data/arxiv_articles.xml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_data)

    return load_from_xml(xml_data)


def load_from_xml(xml_data: str) -> pd.DataFrame:
    file_like = io.StringIO(xml_data)
    df = pd.read_xml(
        file_like,
        xpath="/atom:feed/atom:entry",
        namespaces={"atom": "http://www.w3.org/2005/Atom"},
    )[["id", "title", "summary"]]

    df["author_title"] = "PhD"

    file_like = io.StringIO(xml_data)

    _links_df = pd.read_xml(
        file_like,
        xpath="/atom:feed/atom:entry/atom:link",
        namespaces={"atom": "http://www.w3.org/2005/Atom"},
    )

    return df


if __name__ == "__main__":
    articles_xml = fetch_arxiv_articles(query="electron")
    # Print just the head to avoid massive terminal dumps
    print(articles_xml[:1000])
