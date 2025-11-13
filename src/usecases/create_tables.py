from src.storage.relational_db import Base, engine

Base.metadata.create_all(engine)
