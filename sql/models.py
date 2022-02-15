from sqlalchemy import Column, ForeignKey, String, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import text


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), server_default=text(f"gen_random_uuid()"), primary_key=True)

    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    snippets = relationship("Snippet", back_populates="user")
    token = relationship("Token", back_populates="user", uselist=False)
    quota = relationship("Quota", back_populates="user", uselist=False)


class Quota(Base):
    __tablename__ = "quota"
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    cap = Column(Integer, default=60, nullable=False)
    current = Column(Integer, default=0, nullable=False)
    next_refresh = Column(TIMESTAMP(), server_default=text("now() + interval '1h'"))

    user = relationship("User", back_populates="quota", uselist=False)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # server default is altered to gen_token() in sql.raw
    # due to circular dependency
    access_token = Column(String, unique=True, nullable=False, server_default=text("'temp'"))
    expires = Column(TIMESTAMP(), server_default=text("now() + interval '1h'"))

    user = relationship("User", back_populates="token", uselist=False)


class Snippet(Base):
    __tablename__ = "snippets"
    id = Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    language = Column(String(32), nullable=False)
    code = Column(String(10_000), nullable=False)
    args = Column(String(1_000), nullable=False)

    user = relationship("User", back_populates="snippets")
