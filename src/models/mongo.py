from datetime import datetime
from mongoengine import EmbeddedDocument, IntField, StringField, DateTimeField, EmbeddedDocumentField, Document # pyright: ignore[reportMissingImports]


class Author(EmbeddedDocument): # type: ignore[misc]
    db_id = IntField(required=True)
    full_name = StringField()
    title = StringField()
    

class ScientificArticle(Document): # type: ignore[misc]
    meta = {"collection": "articles",
            "indexes": ["db_id", 
                        "arxiv_id",
                        "$text",
                        ],
            }
    db_id = IntField(required=True)
    
    title = StringField()
    summary = StringField()
    file_path = StringField()
    created_at = DateTimeField()
    
    arxiv_id = StringField()
    
    author = EmbeddedDocumentField(Author)
    text = StringField()