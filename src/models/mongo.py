from mongoengine import EmbeddedDocument, IntField, StringField, DateTimeField, EmbeddedDocumentField, Document


class Author(EmbeddedDocument): # type: ignore[misc]
    id = IntField(required=True)
    full_name = StringField()
    title = StringField()
    

class ScientificArticle(Document): # type: ignore[misc]
    meta = {"collection": "articles", "indexes": ["id", "arxiv_id"]}
    id = IntField(required=True)
    
    title = StringField()
    summary = StringField()
    file_path = StringField()
    created_at = DateTimeField()
    
    arxiv_id = StringField()
    
    author = EmbeddedDocumentField(Author)
    text = StringField()