from typing import NamedTuple


class ScientificArticle(NamedTuple):
    arxiv_id: str
    title: str
    summary: str
    file_path: str
    author_full_name: str
    author_title: str
    db_id: int
    author_db_id: int
