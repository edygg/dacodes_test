from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, SQLModel, select, Session
from passlib.context import CryptContext

from dacodes_test.models.utils import get_utc_timestamp
from dacodes_test.payloads.users import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)


class UserModel(User, table=True):
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        default_factory=get_utc_timestamp,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
        default_factory=get_utc_timestamp,
    )


def verify_user_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(session: Session, username: str):
    query = (
        select(UserModel)
            .where(UserModel.username == username)
            .limit(1)
    )
    results = session.exec(query)
    return results.first()


def create_user(session: Session, user: UserCreate) -> UserModel:
    user_model = UserModel(
        username=user.username,
        email=user.email,
        password_hash=get_user_password_hash(user.password),
    )
    session.add(user_model)
    session.commit()
    session.refresh(user_model)
    return user_model