import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError  # pyright: ignore[reportMissingImports]


class Metadata(BaseModel):
    author: str
    pages: int


class Document(BaseModel):
    id: int
    title: str
    tags: list[str]
    published: bool
    metadata: Metadata | None = None


def load_documents(file_path: Path) -> list[Document]:
    """
    Load and validate documents from a JSON file.

    Args:
        file_path (Path): Path to JSON file.

    Returns:
        list[Document]: List of validated Document objects.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        raw_data: Any = json.load(f)

    documents: list[Document] = []
    for i, item in enumerate(raw_data):
        try:
            doc = Document(**item)
            documents.append(doc)
        except ValidationError as e:
            print(f"Validation error in document index {i}: {e}")

    return documents


def display_documents(documents: list[Document]) -> None:
    """
    Display information about documents, handling missing fields gracefully.

    Args:
        documents (list[Document]): List of Document objects.
    """
    for doc in documents:
        print(f"ID: {doc.id}")
        print(f"Title: {doc.title}")

        if doc.tags:
            tags_str = ", ".join(doc.tags)
        else:
            tags_str = "No tags"

        print(f"Tags: {tags_str}")
        print(f"Published: {doc.published}")

        if doc.metadata:
            print(f"Author: {doc.metadata.author}")
            print(f"Pages: {doc.metadata.pages}")
        else:
            print("Metadata: Not provided")

        print("-" * 40)


def main() -> None:
    """
    Entry point to load and display documents.
    """
    file_path = Path("data/documents.json")
    documents = load_documents(file_path)
    display_documents(documents)


if __name__ == "__main__":
    main()
