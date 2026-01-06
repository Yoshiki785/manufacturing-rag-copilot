"""SQLAlchemy ORM models."""

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Document(Base):
    """Document model representing source documents."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(100))
    source_path: Mapped[str | None] = mapped_column(String(1000))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete")


class Chunk(Base):
    """Chunk model representing text chunks from documents."""

    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_char: Mapped[int | None] = mapped_column(Integer)
    end_char: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    embeddings: Mapped[list["Embedding"]] = relationship(
        back_populates="chunk", cascade="all, delete"
    )


class Embedding(Base):
    """Embedding model for vector representations of chunks."""

    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))
    embedding = mapped_column(Vector(1536))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    chunk: Mapped["Chunk"] = relationship(back_populates="embeddings")


class Thread(Base):
    """Thread model for conversation threads."""

    __tablename__ = "threads"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500))
    user_id: Mapped[str | None] = mapped_column(String(255))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    messages: Mapped[list["Message"]] = relationship(back_populates="thread", cascade="all, delete")


class Message(Base):
    """Message model for individual messages in threads."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    thread_id: Mapped[UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    token_count: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    thread: Mapped["Thread"] = relationship(back_populates="messages")


class AuditLog(Base):
    """Audit log model for system audit trail."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(255))
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
