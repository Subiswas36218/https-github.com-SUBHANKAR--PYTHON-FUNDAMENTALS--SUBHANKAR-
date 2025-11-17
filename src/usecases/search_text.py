import src.storage.mongo  # noqa: F401
from src.models.mongo import ScientificArticle
from src.utils.timeit import timeit


@timeit("Search icontains")
def search_text(keyword: str) -> list[ScientificArticle]:
    return list(ScientificArticle.objects(text__icontains=keyword))


@timeit("Search text index")
def search_text_index(keyword: str) -> list[ScientificArticle]:
    return list(ScientificArticle.objects.search_text(keyword))


# Alias for main.py compatibility
def search_articles(keyword: str) -> list[ScientificArticle]:
    return search_text(keyword)


if __name__ == "__main__":
    results = search_text("galaxies")
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")

    results = search_text_index("galaxies")
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")
