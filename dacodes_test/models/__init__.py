from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
from fastapi import Depends

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def test_data():
    from dacodes_test.models.users import UserModel, get_user_password_hash

    with Session(engine) as session:
        try:
            session.add(UserModel(
                username="edygg_1",
                email="efgm1024@gmail.com",
                password_hash=get_user_password_hash("password"),
            ))
            session.add(UserModel(
                username="edygg_2",
                email="efgm1025@gmail.com",
                password_hash=get_user_password_hash("password"),
            ))
            session.add(UserModel(
                username="edygg_3",
                email="efgm1026@gmail.com",
                password_hash=get_user_password_hash("password"),
            ))
            session.commit()
        except:
            pass

