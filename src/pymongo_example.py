import json
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, TypeAdapter, field_validator
from bson import ObjectId
from pymongo import MongoClient

MONGO_URL = "mongodb://root:samindia@localhost:27017/?authSource=admin"

client: MongoClient[dict[str, Any]] = MongoClient(MONGO_URL)
users_col = client.PythonDE.users


class Profile(BaseModel):
    age: int | None = None
    city: str | None = None
    interests: list[str] | None = None


class MongoUser(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: str
    profile: Profile | None = None
    created_at: datetime | None = None  # Optional for missing timestamps

    model_config = {"populate_by_name": True}  # NEW LINE

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, v: Any) -> str | None:
        return v.isoformat() if isinstance(v, datetime) else v


    
    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v: Any) -> datetime | None:
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return None
        return v


MongoUserList = TypeAdapter(list[MongoUser])


def list_users() -> list[MongoUser]:
    users = list(users_col.find())
    cleaned_users = MongoUserList.validate_python(users)
    return cleaned_users


def get_user_by_username(username: str) -> MongoUser | None:
    user_data = users_col.find_one({"username": username})
    if user_data:
        return MongoUser.model_validate(user_data)
    return None


if __name__ == "__main__":
    users = list_users()

    # Export clean JSON with ISO timestamps
    json_bytes = MongoUserList.dump_json(users, indent=2)

    with open("data/mongo_users.json", "wb") as f:
        f.write(json_bytes)

    print("Exported users to data/mongo_users.json")

    user = get_user_by_username("alice")
    print("Mongo user with username 'alice':", user)

        

