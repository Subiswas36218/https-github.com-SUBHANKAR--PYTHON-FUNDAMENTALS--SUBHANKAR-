import src.storage.mongo  # noqa: F401
from src.models.mongo import ScientificArticle
from src.utils.timeit import timeit

@timeit("Search icontains")
def search_text(keyword: str) -> list[ScientificArticle]:
    query = ScientificArticle.objects(text__icontains=keyword)
    return list(query)

@timeit("Search text index")
def search_text_index(keyword: str) -> list[ScientificArticle]:
    query = ScientificArticle.objects.search_text(keyword)
    return list(query)

if __name__ == "__main__":
    results = search_text("galaxies")
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")
        
    results = search_text_index("galaxies")
    for article in results:
        print(f"{article.arxiv_id}: {article.title}")        
    