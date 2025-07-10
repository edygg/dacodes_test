from typing import Annotated
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession as Session

from fastapi import Depends

sqlite_file_name = "database.db"
sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"

engine = create_async_engine(sqlite_url)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


async def test_data():
    from dacodes_test.models.users import UserModel, get_user_password_hash

    async with Session(engine) as session:
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
            await session.commit()
        except:
            pass

