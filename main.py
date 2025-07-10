from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, status

from dacodes_test.auth.jwt import OAuth2LoginDep, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    Token
from dacodes_test.models import SessionDep, create_db_and_tables, test_data
from dacodes_test.models.users import User, create_user
from dacodes_test.payloads.users import UserCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    test_data()
    yield

app = FastAPI(
    title="Dacodes API Test by Edilson Gonzalez",
    lifespan=lifespan,
)


@app.get("/health-check")
async def health_check():
    return {"status": "ok"}


@app.post("/auth/register", response_model=User)
async def register_user(
        user: UserCreate,
        session: SessionDep,
):
    return create_user(session, user)


@app.post("/auth/login", response_model=Token)
async def login_user(
        form_data: OAuth2LoginDep,
        session: SessionDep,
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")