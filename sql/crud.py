from sqlalchemy.orm import Session
from . import models
from . import schemas
from argon2 import PasswordHasher
import secrets


hasher = PasswordHasher()


class User:
    @staticmethod
    def get_by_id(session: Session, id: int) -> schemas.User:
        return session.query(models.User).filter(models.User.id == id).first()

    @staticmethod
    def create(session: Session, user: schemas.UserCreate):
        password_hash = hasher.hash(user.password)
        db_user = models.User(
            email=user.email, password_hash=password_hash,
            token=secrets.token_urlsafe()
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    @staticmethod
    def update_by_id(session: Session, user: schemas.UserCreate):
        db_user: models.User = session.query(models.User).filter(models.User.id == user.id).first()
        db_user.email = user.email
        db_user.password_hash = hasher.hash(user.password)

        pass

    @staticmethod
    def delete_by_id():
        pass


class Snippet:
    model = models.Snippet

    @staticmethod
    def get_by_id():
        pass
