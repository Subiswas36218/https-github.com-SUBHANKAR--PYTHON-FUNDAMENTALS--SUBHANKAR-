from typing import List

from src.models.mongo import ScientificArticle
import src.storage.mongo  # noqa: F401

def list_articles() -> List[ScientificArticle]:
    return ScientificArticle.objects.all()  # type: ignore[return-value]

if __name__ == "__main__":
    print(list_articles())