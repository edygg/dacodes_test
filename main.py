from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, status, Query

from dacodes_test.auth.jwt import OAuth2LoginDep, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    Token, CurrentUserDep
from dacodes_test.models import SessionDep, create_db_and_tables, test_data
from dacodes_test.models.games import GameSessionModel, start_game_session, stop_game_session, calc_leaderboard, \
    user_game_history, has_game_history
from dacodes_test.models.users import User, create_user, get_user_by_id
from dacodes_test.payloads.users import UserCreate
from dacodes_test.responses.leaderboards import LeaderboardUserStatsItem, UserStatsAndHistory


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    # await test_data()
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
    return await create_user(session, user)


@app.post("/auth/login", response_model=Token)
async def login_user(
        form_data: OAuth2LoginDep,
        session: SessionDep,
):
    user = await authenticate_user(session, form_data.username, form_data.password)
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


@app.post("/games/start", response_model=GameSessionModel)
async def start_game(
        current_user: CurrentUserDep,
        session: SessionDep,
):
    return await start_game_session(
        session,
        current_user.id,
    )


@app.post("/games/{game_session_id}/stop", response_model=GameSessionModel)
async def stop_game(
        game_session_id: int,
        session: SessionDep,
        current_user: CurrentUserDep,
):
    game_session = await stop_game_session(
        session,
        game_session_id,
        current_user.id,
    )

    if not game_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found.",
        )

    return game_session


@app.get("/leaderboard", response_model=list[LeaderboardUserStatsItem])
async def get_leaderboard(
        session: SessionDep,
        page: int = Query(default=1),
        per_page: int = Query(default=10),
):
    return await calc_leaderboard(session, page, per_page)


@app.get("/analytics/user/{user_id}", response_model=UserStatsAndHistory)
async def get_user_game_history(
        user_id: int,
        session: SessionDep,
):
    user = await get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found.",
        )

    has_games = await has_game_history(session, user_id)

    if not has_games:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No games found.",
        )

    return await user_game_history(session, user_id)
