from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, Session, SQLModel, select

from dacodes_test.models.utils import get_utc_timestamp
from dacodes_test.models.users import UserModel


class GameSessionStatus:
    ACTIVE = "active"
    STOPPED = "stopped"
    EXPIRED = "expired"


class GameSession(SQLModel):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="usermodel.id")
    start_time: datetime = Field(
        sa_column=Column(
            "start_time",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        default_factory=get_utc_timestamp,
    )
    stop_time: datetime = Field(
        sa_column=Column(
            "stop_time",
            TIMESTAMP(timezone=True),
            nullable=True,
        )
    )
    status: str = Field(default=GameSessionStatus.ACTIVE, nullable=False)
    duration: float = Field(default=0.0, nullable=True)
    deviation: float = Field(default=0.0, nullable=True)


class GameSessionModel(GameSession, table=True):
    pass


def start_game_session(session: Session, user_id: int):
    query = (
        select(GameSessionModel)
            .where(GameSessionModel.user_id == user_id)
            .where(GameSessionModel.status == GameSessionStatus.ACTIVE)
    )

    results = session.exec(query)
    has_active_game_session = results.first()

    if has_active_game_session:
        return has_active_game_session

    game_session = GameSessionModel(user_id=user_id)
    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    return game_session


def stop_game_session(session: Session, game_session_id: int) -> GameSessionModel | None:
    EXPIRED_THRESHOLD_IN_SECONDS = 30 * 60 * 60  # 30 minute in seconds

    query = (
        select(GameSessionModel)
            .where(GameSessionModel.id == game_session_id)
            .where(GameSessionModel.status == GameSessionStatus.ACTIVE)
    )

    results = session.exec(query)
    game_session = results.first()

    if not game_session:
        return None

    game_session.stop_time = get_utc_timestamp()
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    delta_time = game_session.stop_time - game_session.start_time

    game_session.status = GameSessionStatus.STOPPED if delta_time.seconds < EXPIRED_THRESHOLD_IN_SECONDS else GameSessionStatus.EXPIRED
    calc_duration_in_milliseconds = delta_time.days * 86400000 + delta_time.seconds * 1000 + delta_time.microseconds // 1000
    calc_deviation_in_milliseconds = abs(calc_duration_in_milliseconds - 10000) # 10 seconds in milliseconds
    game_session.duration = calc_duration_in_milliseconds
    game_session.deviation = calc_deviation_in_milliseconds

    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    return game_session


def calc_leaderboard(session: Session, page: int = 1, per_page: int = 10):
    subquery = (
        session.query(
            GameSessionModel.user_id,
            func.count(GameSessionModel.id).label("total_games"),
            func.avg(GameSessionModel.deviation).label("avg_deviation"),
            func.min(GameSessionModel.deviation).label("best_deviation")
        )
        .group_by(GameSessionModel.user_id)
        .subquery()
    )

    query = (
        session.query(
            UserModel.username,
            subquery.c.total_games,
            subquery.c.avg_deviation,
            subquery.c.best_deviation
        )
        .join(subquery, UserModel.id == subquery.c.user_id)
        .order_by(subquery.c.avg_deviation.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    results = query.all()

    leaderboard = [
        {
            "username": row.username,
            "total_games": row.total_games,
            "average_deviation": float(row.avg_deviation),
            "best_deviation": float(row.best_deviation),
        }
        for row in results
    ]
    return leaderboard


def user_game_history(session: Session, user_id: int):
    subquery = (
        session.query(
            GameSessionModel.user_id,
            func.count(GameSessionModel.id).label("total_games"),
            func.avg(GameSessionModel.deviation).label("avg_deviation"),
            func.min(GameSessionModel.deviation).label("best_deviation")
        )
        .where(GameSessionModel.user_id == user_id)
        .group_by(GameSessionModel.user_id)
        .subquery()
    )

    stats_query = (
        session.query(
            UserModel.username,
            subquery.c.total_games,
            subquery.c.avg_deviation,
            subquery.c.best_deviation
        )
        .join(subquery, UserModel.id == subquery.c.user_id)
        .where(subquery.c.user_id == user_id)
    )

    stats = stats_query.first()

    game_history_query = (
        select(GameSessionModel)
            .where(GameSessionModel.user_id == user_id)
    )
    game_history = session.exec(game_history_query).all()
    
    return {
        "username": stats.username,
        "total_games": stats.total_games,
        "average_deviation": float(stats.avg_deviation),
        "best_deviation": float(stats.best_deviation),
        "history": [g.dict() for g in game_history],
    }
