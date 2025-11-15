from src.models.mongo import ScientificArticle
import src.storage.mongo  # noqa: F401


def list_articles():
    return ScientificArticle.objects.all()


if __name__ == "__main__":
    print(list_articles())