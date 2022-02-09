import uuid
from sqlalchemy.orm import Session
from . import models
from . import schemas
# noinspection PyPackageRequirements
from argon2 import PasswordHasher
import secrets


hasher = PasswordHasher()


class Crud:
    session: Session

    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self) -> Session:
        return self.session


class User(Crud):
    def get_by_id(self, id: uuid.UUID) -> schemas.User:
        return self.session.query(models.User).filter(models.User.id == id).first()

    def create(self, user: schemas.UserCreate) -> schemas.User:
        db_user = models.User(
            email=user.email, password_hash=hasher.hash(user.password),
            token=secrets.token_urlsafe()
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def update_by_id(self, id: uuid.UUID, user: schemas.UserCreate) -> schemas.User:
        db_user: models.User = self.session.query(models.User).filter(models.User.id == id).first()
        db_user.email = user.email
        db_user.password_hash = hasher.hash(user.password)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def delete_by_id(self, id: uuid.UUID) -> schemas.User:
        db_user: models.User = self.session.query(models.User).filter(models.User.id == id).first()
        self.session.delete(db_user)
        self.session.commit()
        return db_user


class Snippet(Crud):
    def get_by_id(self, id: uuid.UUID) -> schemas.Snippet:
        return self.session.query(models.Snippet).filter(models.Snippet.id == id).first()

    def create(self, snippet: schemas.SnippetCreate) -> schemas.Snippet:
        db_snippet = models.Snippet(
            **snippet.dict()
        )
        self.session.add(db_snippet)
        self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def update_by_id(self, id: uuid.UUID, snippet: schemas.SnippetCreate) -> schemas.Snippet:
        db_snippet: models.Snippet = self.session.query(models.Snippet).filter(models.Snippet.id == id).first()
        db_snippet.language = snippet.language
        db_snippet.code = snippet.code
        db_snippet.args = snippet.args
        self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def delete_by_id(self, id: uuid.UUID) -> schemas.Snippet:
        db_snippet: models.Snippet = self.session.query(models.Snippet).filter(models.Snippet.id == id).first()
        self.session.delete(db_snippet)
        self.session.commit()
        return db_snippet
