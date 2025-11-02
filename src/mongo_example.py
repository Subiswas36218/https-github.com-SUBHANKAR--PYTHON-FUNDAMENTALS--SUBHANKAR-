from typing import Any
from pymongo import MongoClient, errors
from mongoengine import (
    Document, 
    StringField, 
    IntField,
    EmbeddedDocument, 
    EmbeddedDocumentField,
    DateTimeField, 
    connect, 
    ListField, 
    EmbeddedDocumentListField
)
from mongoengine.errors import FieldDoesNotExist, ValidationError
from datetime import datetime

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"

client: MongoClient[dict[str, Any]] = MongoClient(MONGO_URL)
users_col = client.PythonDE.users

# Clean malformed documents (auto-fix and deduplicate)
bad_docs = list(users_col.find({"0": {"$exists": True}}))
if bad_docs:
    print(f"Found {len(bad_docs)} malformed document(s). Cleaning up...")
    for bad_doc in bad_docs:
        fixed_doc = bad_doc.get("0", {})
        if not fixed_doc:
            users_col.delete_one({"_id": bad_doc["_id"]})
            continue

        username = fixed_doc.get("username")
        # Check if a valid doc with same username already exists
        if username and users_col.find_one({"username": username, "0": {"$exists": False}}):
            print(f"Duplicate username '{username}' found. Removing malformed document.")
            users_col.delete_one({"_id": bad_doc["_id"]})
        else:
            print(f"Fixing malformed document for user '{username}'.")
            users_col.update_one(
                {"_id": bad_doc["_id"]},
                {"$set": fixed_doc, "$unset": {"0": ""}}
            )
    print("Cleanup completed.")


print("\nExisting users in MongoDB:")
for user in users_col.find():
    print(dict(user))


new_user = {
    "username": "charlie",
    "email": "charlie@example.com",
    "profile": {
        "age": 30,
        "interests": ["hiking", "photography"]
    },
    "orders": [
        {
            "order_id": 1,
            "product": "Camera",
            "amount": 2000
        }
    ]
}

try:
    if users_col.find_one({"username": new_user["username"]}):
        print(f"\nUser '{new_user['username']}' already exists. Skipping insert.")
    else:
        insert_result = users_col.insert_one(new_user)
        print("Inserted user ID:", insert_result.inserted_id)

except errors.DuplicateKeyError:
    print(f"Duplicate username '{new_user['username']}' detected. Insert skipped.")
except Exception as e:
    print("An error occurred during insert:", e)


connect(db="PythonDE", host=MONGO_URL)

class Order(EmbeddedDocument):
    order_id = IntField(required=True)
    product = StringField(required=True)
    amount = IntField(min_value=0)

class Profile(EmbeddedDocument):
    age = IntField(min_value=0, max_value=120)
    city = StringField(max_length=100)
    interests = ListField(StringField())

class User(Document): # Type: ignore[misc]
    meta = {
        'collection': 'users',
        'indexes': ['username', 'email']
    }

    username = StringField(required=True, unique=True, max_length=50) # Type: ignore[misc]
    email = StringField(required=True, unique=True)
    profile = EmbeddedDocumentField(Profile)
    created_at = DateTimeField(default=datetime.utcnow)
    orders = EmbeddedDocumentListField(Order)

result = User.objects
for engine_user in result:
    print("MongoEngine User:", engine_user.username, engine_user.profile.city if engine_user.profile else "N/A")

print("\nExisting users via MongoEngine:")
try:
    for user in User.objects():
        print(user.to_json())
except (FieldDoesNotExist, ValidationError) as e:
    print("Skipped malformed document:", e)
except Exception as e:
    print("Unexpected error:", e)
