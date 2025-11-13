from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.storage.relational_db import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100))

    articles = relationship("ScientificArticle", back_populates="author")


class ScientificArticle(Base):
    __tablename__ = "scientific_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text) # can Hold very long titles
    summary: Mapped[str] = mapped_column(Text) # can Hold very long summaries
    file_path: Mapped[str] = mapped_column(String(500))
   
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    arxiv_id: Mapped[str] = mapped_column(String(50), unique=True)

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=True)
    author = relationship("Author", back_populates="articles")
