from typing import *
import uuid
from sqlalchemy import exc
from sqlalchemy.orm import Session
from . import models
import schemas
from . import errors
# noinspection PyPackageRequirements
from argon2 import PasswordHasher
from fastapi.security import OAuth2PasswordRequestForm


hasher = PasswordHasher()


class Crud:
    session: Session

    def __init__(self, session: Session, token: Optional[schemas.token.Token] = None) -> None:
        self.session = session
        self.token = token

    def __enter__(self) -> "Crud":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class User(Crud):
    def get_by_id(self, id: uuid.UUID) -> Optional[models.User]:
        return user if (
            user := self.session.query(models.User).filter(models.User.id == id).first()
        ) else None

    def get_by_email(self, email: str) -> Optional[models.User]:
        return user if (
            user := self.session.query(models.User).filter(models.User.email == email).first()
        ) else None

    def get_by_token(self, token: str) -> Optional[models.User]:
        return user if (
            user := self.session.query(models.User).filter(models.User.token == token).first()
        ) else None

    def create(self, user: OAuth2PasswordRequestForm) -> models.User:
        db_user = models.User(
            email=user.username, password_hash=hasher.hash(user.password),
        )
        try:
            self.session.add(db_user)
            self.session.commit()
        except exc.IntegrityError:
            raise errors.DuplicateEmail(user.username)
        self.session.refresh(db_user)
        return db_user

    def update_by_id(self, id: uuid.UUID, user: schemas.user.UserAuthData) -> Optional[models.User]:
        db_user = self.get_by_id(id)
        if not db_user or self.token != db_user.token:
            return
        try:
            db_user.email = user.email
            db_user.password_hash = hasher.hash(user.password)
            self.session.commit()
        except exc.IntegrityError:
            raise errors.DuplicateEmail(user.email)
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
        return token if (
            token := self.session.query(models.Token).filter(models.Snippet.id == id).first()
        ) else None

    def get_by_access_token(self, access_token: str) -> Optional[models.Token]:
        return token if (
            token := self.session.query(models.Token).filter(models.Token.access_token == access_token).first()
        ) else None

    def create(self, user: models.User) -> None:
        if user.token:
            return self.update(user.token)
        token = models.Token(user=user)
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

    def update(self, token: schemas.token.Token) -> None:
        self.session.execute("select update_expiration_of_row(:id);", {"id": token.id})
        self.session.commit()
        self.session.refresh(token)

    def delete_by_id(self, id: int) -> Optional[models.Token]:
        db_token = self.get_by_id(id)
        if not db_token:
            return
        self.session.delete(db_token)
        self.session.commit()
        return db_token

    def delete_by_value(self, access_token: str) -> Optional[models.Token]:
        db_token: models.Token = self.session.query(models.Token).filter(models.Token.access_token == access_token).first()
        if not db_token:
            return
        self.session.delete(db_token)
        self.session.commit()
        return db_token


class Quota(Crud):
    def get_by_id(self, id: int) -> Optional[models.Quota]:
        return quota if (
            quota := self.session.query(models.Quota).filter(models.Quota.id == id).first()
        ) else None

    def create(self, user: models.User) -> None:
        if user.quota:
            return
        quota = models.Quota(user=user)
        self.session.add(quota)
        self.session.commit()
        self.session.refresh(quota)

    def update(self, quota: models.Quota) -> None:
        pass

    def delete_by_id(self, id: int) -> Optional[models.Quota]:
        db_quota: models.Quota = self.session.query(models.Quota).filter(models.Quota.id == id).first()
        if not db_quota:
            return
        self.session.delete(db_quota)
        self.session.commit()
        return db_quota


class Snippet(Crud):
    def get_by_id(self, id: uuid.UUID) -> Optional[models.Snippet]:
        return snippet if (
            snippet := self.session.query(models.Snippet).filter(models.Snippet.id == id).first()
        ) else None

    def create(self, user: models.User, snippet: schemas.snippet.SnippetData) -> models.Snippet:
        db_snippet = models.Snippet(
            **snippet.dict(),
            user=user
        )
        try:
            self.session.add(db_snippet)
            self.session.commit()
        except exc.IntegrityError:
            # the slim chance that there is a duplicate uuid
            # retry once
            self.session.add(db_snippet)
            self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def update_by_id(self, id: uuid.UUID, snippet: schemas.snippet.SnippetData) -> Optional[models.Snippet]:
        db_snippet: models.Snippet = self.get_by_id(id)
        if not db_snippet or self.token != db_snippet.user.token:
            return
        db_snippet.language = snippet.language
        db_snippet.code = snippet.code
        db_snippet.args = snippet.args
        self.session.commit()
        self.session.refresh(db_snippet)
        return db_snippet

    def delete_by_id(self, id: uuid.UUID) -> Optional[models.Snippet]:
        db_snippet = self.get_by_id(id)
        if not db_snippet:
            return
        self.session.delete(db_snippet)
        self.session.commit()
        return db_snippet
