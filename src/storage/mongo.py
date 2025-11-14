from mongoengine import connect

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"
connect(db="PythonDE", host=MONGO_URL)