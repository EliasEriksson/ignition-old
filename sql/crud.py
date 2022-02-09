import uuid
from sqlalchemy import text, bindparam
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
    @staticmethod
    def refresh_token(session: Session, user: models.User) -> None:
        if user.token:
            session.execute("select update_expiration_of_row(:id);", {"id": user.token.id})
            return
        token = models.Token(user=user)
        session.add(token)

    def get_by_id(self, id: uuid.UUID) -> schemas.User:
        db_user: models.User = self.session.query(models.User).filter(models.User.id == id).first()
        self.refresh_token(self.session, db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def get_by_email(self, email: str) -> schemas.User:
        db_user: models.User = self.session.query(models.User).filter(models.User.email == email).first()
        self.refresh_token(self.session, db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return schemas.User(id=db_user.id, email=db_user.email, token=db_user.token)

    def create(self, user: schemas.UserAuth) -> schemas.User:
        db_user = models.User(
            email=user.email, password_hash=hasher.hash(user.password),
        )
        self.refresh_token(self.session, db_user)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return schemas.User(id=db_user.id, email=db_user.email, token=db_user.token)

    def update_by_id(self, id: uuid.UUID, user: schemas.UserAuth) -> schemas.User:
        db_user = self.get_by_id(id)
        db_user.email = user.email
        db_user.password_hash = hasher.hash(user.password)
        self.refresh_token(self.session, db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def delete_by_id(self, id: uuid.UUID) -> schemas.User:
        db_user = self.get_by_id(id)
        self.session.delete(db_user)
        self.session.commit()
        return db_user


class Token(Crud):
    def get_by_id(self, id: int) -> schemas.Token:
        return self.session.query(models.Token).filter(models.Snippet.id == id).first()

    def delete_by_id(self, id: int) -> schemas.Token:
        db_token = self.get_by_id(id)
        self.session.delete(db_token)
        self.session.commit()
        return db_token

    def delete_by_value(self, value: str) -> schemas.Token:
        db_token: models.Token = self.session.query(models.Token).filter(models.Token.value == value).first()
        self.session.delete(db_token)
        self.session.commit()
        return db_token


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
        db_snippet = self.get_by_id(id)
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
