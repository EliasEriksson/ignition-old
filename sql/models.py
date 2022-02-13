from sqlalchemy import Column, ForeignKey, String, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import text


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), server_default=text(f"gen_random_uuid()"), primary_key=True)

    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    snippets = relationship("Snippet", back_populates="user")
    token = relationship("Token", back_populates="user", uselist=False)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    value = Column(String, unique=True, nullable=False, server_default=text(f"gen_token('tokens')"))  # server default gen_token()
    expires = Column(TIMESTAMP(), server_default=text("now() + interval '1h'"))

    user = relationship("User", back_populates="token", uselist=False)


class Snippet(Base):
    __tablename__ = "snippets"
    id = Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    language = Column(String, nullable=False)
    code = Column(String, nullable=False)
    args = Column(String, nullable=False)

    user = relationship("User", back_populates="snippets")
