from src.storage.relational_db import Base, engine
from models.relational import Author, ScientificArticle  # noqa: F401

Base.metadata.create_all(engine)
