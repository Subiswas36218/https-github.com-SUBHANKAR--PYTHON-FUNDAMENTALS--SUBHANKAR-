from src.models.relational import Author, ScientificArticle  # noqa: F401
from src.storage.relational_db import Base, engine

Base.metadata.create_all(engine)
