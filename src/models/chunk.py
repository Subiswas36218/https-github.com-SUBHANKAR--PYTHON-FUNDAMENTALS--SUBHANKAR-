from pydantic import BaseModel


class ScientificArticleChunk(BaseModel):
    title: str
    summary: str
    arxiv_id: str
    author_full_name: str

    chunk_text: str
    chunk_index: int
