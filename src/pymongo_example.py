from typing import Any
from pymongo import MongoClient, errors


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