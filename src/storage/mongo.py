from mongoengine import connect # pyright: ignore[reportMissingImports]

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"

connect(
    db="PythonDE",
    host=MONGO_URL,
    alias="default"
)
