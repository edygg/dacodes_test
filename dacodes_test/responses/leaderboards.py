from pydantic import BaseModel


class LeaderboardUserStatsItem(BaseModel):
    username: str
    total_games: int
    average_deviation: float
    best_deviation: float


class UserStatsAndHistory(LeaderboardUserStatsItem):
    history: list[dict]