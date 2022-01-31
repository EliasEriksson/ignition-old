from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .database import Base
from argon2 import PasswordHasher
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)

    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    token = Column(UUID(as_uuid=True), unique=True, nullable=False)

    snippets = relationship("Snippet", back_populates="snippet")


class Snippet(Base):
    __tablename__ = "snippets"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    language = Column(String, nullable=False)
    code = Column(String, nullable=False)
    args = Column(String, nullable=False)

    user = relationship("User", back_populates="snippets", cascade="all, delete-orphan")
