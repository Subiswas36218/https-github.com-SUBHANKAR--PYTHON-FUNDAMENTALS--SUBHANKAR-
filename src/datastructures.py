from dataclasses import dataclass, field
from typing import NamedTuple


# ---------------------------
# NamedTuple: Immutable User
# ---------------------------
class User(NamedTuple):
    id: int
    name: str
    email: str


# Correct call: "id", not "user_id"
user = User(id=1, name="John Doe", email="email@site.com")


# ---------------------------
# Dataclass: Mutable User
# ---------------------------
@dataclass
class DataClassUser:
    user_id: int
    username: str
    email: str
    is_active: bool = False
    tags: list[str] = field(default_factory=list)


data_class_user = DataClassUser(
    user_id=2, username="Jane Doe", email="jane@example.com"
)
