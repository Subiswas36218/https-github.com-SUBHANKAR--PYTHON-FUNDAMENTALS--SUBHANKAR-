
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

try:
    for user in User.objects():
        print(user.to_json())
except (FieldDoesNotExist, ValidationError) as e:
    print("Skipped malformed document:", e)
except Exception as e:
    print("Unexpected error:", e)
