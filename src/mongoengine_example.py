from datetime import datetime

from bson import ObjectId
from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    IntField,
    ListField,
    StringField,
    connect,
)
from mongoengine.errors import FieldDoesNotExist, ValidationError

from pymongo_example import MongoUser, MongoUserList  # for type comparison only

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"
connect(db="PythonDE", host=MONGO_URL)


class Order(EmbeddedDocument):
    order_id = IntField(required=True)
    product = StringField(required=True)
    amount = IntField(min_value=0)


class Profile(EmbeddedDocument):
    age = IntField(min_value=0, max_value=120)
    city = StringField(max_length=100)
    interests = ListField(StringField())


class User(Document):  # type: ignore[misc]
    meta = {"collection": "users", "indexes": ["username", "email"]}

    username = StringField(required=True, unique=True, max_length=50)  # type: ignore[misc]
    email = StringField(required=True, unique=True)
    profile = EmbeddedDocumentField(Profile)
    created_at = DateTimeField(default=datetime.utcnow)
    orders = EmbeddedDocumentListField(Order)


def list_users() -> list[MongoUser]:
    """Convert MongoEngine User objects to dictionaries before validating."""
    mongo_users = []

    for user in User.objects.all():
        user_dict = user.to_mongo().to_dict()

        # Convert ObjectId to string
        if isinstance(user_dict.get("_id"), ObjectId):
            user_dict["_id"] = str(user_dict["_id"])

        mongo_users.append(user_dict)

    return MongoUserList.validate_python(mongo_users)


if __name__ == "__main__":
    print("All users in MongoDB:")

    try:
        users = list_users()
        for user in users:
            print(
                f"[{user.id}] Username: {user.username}, Email: {user.email}, Created At: {user.created_at}"
            )

        with open("data/mongoengine_users.json", "wb") as f:
            f.write(MongoUserList.dump_json(users, indent=2))

        print("Exported users to data/mongoengine_users.json")

    except (FieldDoesNotExist, ValidationError) as e:
        print("Skipped malformed document:", e)
    except Exception as e:
        print("Unexpected error:", e)
