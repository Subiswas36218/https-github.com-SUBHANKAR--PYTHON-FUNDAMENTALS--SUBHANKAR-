from datetime import datetime
from pathlib import Path
from typing import Any

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

from src.pymongo_example import MongoUser, MongoUserList

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"
connect(db="PythonDE", host=MONGO_URL)


class Order(EmbeddedDocument):  # type: ignore
    order_id = IntField(required=True)
    product = StringField(required=True)
    amount = IntField(min_value=0)


class Profile(EmbeddedDocument):  # type: ignore
    age = IntField(min_value=0, max_value=120)
    city = StringField(max_length=100)
    interests = ListField(StringField())


class User(Document):  # type: ignore
    meta = {"collection": "users", "indexes": ["username", "email"]}

    username = StringField(required=True, unique=True, max_length=50)
    email = StringField(required=True, unique=True)
    profile = EmbeddedDocumentField(Profile)
    created_at = DateTimeField(default=datetime.utcnow)
    orders = EmbeddedDocumentListField(Order)


def list_users() -> list[MongoUser]:
    """Load all MongoEngine users → convert → validate → return list."""
    converted: list[dict[str, Any]] = []

    for user in User.objects.all():
        doc = user.to_mongo().to_dict()

        if isinstance(doc.get("_id"), ObjectId):
            doc["_id"] = str(doc["_id"])

        converted.append(doc)

    validated = MongoUserList.validate_python(converted)
    return validated


def main() -> None:
    print("All users in MongoDB:\n")

    try:
        users = list_users()
        for user in users:
            print(
                f"[{user.id}] Username: {user.username}, "
                f"Email: {user.email}, Created At: {user.created_at}"
            )

        output_path = Path("data/mongoengine_users.json")
        output_path.write_bytes(MongoUserList.dump_json(users, indent=2))

        print(f"\nExported users → {output_path}")

    except (FieldDoesNotExist, ValidationError) as e:
        print("Skipped malformed document:", e)

    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    main()
