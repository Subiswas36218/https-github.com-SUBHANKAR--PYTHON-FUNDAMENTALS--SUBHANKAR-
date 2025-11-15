from typing import List
from src.models.mongo import ScientificArticle
import src.storage.mongo  # noqa: F401


def list_articles() -> list[ScientificArticle]:
    return list(ScientificArticle.objects.all())


if __name__ == "__main__":
    for a in list_articles():
        preview = (a.text or "").strip()  # ensures no crash
        print(f"{a.arxiv_id}: {preview[:100]}")

    