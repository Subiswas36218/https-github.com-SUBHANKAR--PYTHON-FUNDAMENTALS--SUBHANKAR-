from __future__ import annotations

import requests

URL = "http://export.arxiv.org/api/query"


def fetch_arxiv_articles(
    query: str = "electron", start: int = 0, max_results: int = 10
) -> str:
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
    params: dict[str, str] = {
        "search_query": f"all:{query}",
        "start": str(int(start)),
        "max_results": str(int(max_results)),
    }

    resp = requests.get(URL, params=params, timeout=10)
    resp.raise_for_status()

    xml_data = resp.text

    # Ensure output directory exists (simple path write)
    out_path = "data/arxiv_articles.xml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_data)

    return xml_data


if __name__ == "__main__":
    articles_xml = fetch_arxiv_articles()
    # Print just the head to avoid massive terminal dumps
    print(articles_xml[:1000])
