from typing import *
import uuid
from sqlalchemy.orm import Session
from . import models
from . import schemas
# noinspection PyPackageRequirements
from argon2 import PasswordHasher


hasher = PasswordHasher()


class Crud:
    session: Session

    def __init__(self, session: Session, token: Optional[schemas.Token] = None) -> None:
        self.session = session
        self.token = token

    def __enter__(self) -> "Crud":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class User(Crud):
    def get_by_id(self, id: uuid.UUID) -> Optional[models.User]:
        return self.session.query(models.User).filter(models.User.id == id).first()

    def get_by_email(self, email: str) -> Optional[models.User]:
        return self.session.query(models.User).filter(models.User.email == email).first()

    def get_by_token(self, token: str) -> Optional[models.User]:
        return self.session.query(models.User).filter(models.User.token == token).first()

    def create(self, user: schemas.UserAuth) -> models.User:
        db_user = models.User(
            email=user.email, password_hash=hasher.hash(user.password),
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def update_by_id(self, id: uuid.UUID, user: schemas.UserAuth) -> Optional[models.User]:
        db_user = self.get_by_id(id)
        if not db_user or self.token != db_user.token:
            return

        db_user.email = user.email
        db_user.password_hash = hasher.hash(user.password)
        self.session.commit()
        return db_user

    def delete_by_id(self, id: uuid.UUID) -> Optional[models.User]:
        db_user = self.get_by_id(id)
        if not db_user or self.token != db_user.token:
            return
        self.session.delete(db_user)
        self.session.commit()
        return db_user


class Token(Crud):
    def get_by_id(self, id: int) -> Optional[models.Token]:
        return token if (token := self.session.query(models.Token).filter(models.Snippet.id == id).first()) else None

    def get_by_header(self, authorization_header: str) -> Optional[models.Token]:
        return self.get_by_value(authorization_header.lstrip("Bearer:").strip())

    def get_by_value(self, value: str) -> Optional[models.Token]:
        return token if (token := self.session.query(models.Token).filter(models.Token.value == value).first()) else None

    def create(self, user: models.User) -> None:
        if user.token:
            return self.update(user)
        token = models.Token(user=user)
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

    def update(self, user: models.User) -> None:
        if user.token:
            self.session.execute("select update_expiration_of_row(:id);", {"id": user.token.id})
            self.session.commit()
            self.session.refresh(user.token)

    def delete_by_id(self, id: int) -> Optional[models.Token]:
        db_token = self.get_by_id(id)
        self.session.delete(db_token)
        self.session.commit()
        return db_token

    def delete_by_value(self, value: str) -> Optional[models.Token]:
        db_token: models.Token = self.session.query(models.Token).filter(models.Token.value == value).first()
        self.session.delete(db_token)
        self.session.commit()
        return db_token


class Snippet(Crud):
    def get_by_id(self, id: uuid.UUID) -> Optional[models.Snippet]:
        return self.session.query(models.Snippet).filter(models.Snippet.id == id).first()

    def create(self, user: models.User, snippet: schemas.SnippetCreate) -> models.Snippet:
        db_snippet = models.Snippet(
            **snippet.dict(),
            user=user
        )
        self.session.add(db_snippet)
        self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def update_by_id(self, id: uuid.UUID, snippet: schemas.SnippetCreate) -> Optional[models.Snippet]:
        db_snippet: models.Snippet = self.get_by_id(id)
        if not db_snippet or self.token != db_snippet.user.token:
            return
        db_snippet.language = snippet.language
        db_snippet.code = snippet.code
        db_snippet.args = snippet.args
        self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def delete_by_id(self, id: uuid.UUID) -> schemas.Snippet:
        db_snippet = self.get_by_id(id)
        self.session.delete(db_snippet)
        self.session.commit()
        return db_snippet
