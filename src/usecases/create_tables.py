from src.storage.relational_db import Base, engine
from src.models.relational import Author, ScientificArticle

Base.metadata.create_all(engine)