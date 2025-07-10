import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import select

from dacodes_test.models.games import (
    GameSessionModel,
    GameSessionStatus,
    start_game_session,
    stop_game_session,
    calc_leaderboard,
    user_game_history,
    has_game_history,
)
from dacodes_test.models.users import UserModel
from dacodes_test.models.utils import get_utc_timestamp


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_start_game_session_new(mock_session):
    """Test start_game_session when user has no active game session."""
    # Arrange
    user_id = 1

    # Mock the query execution for checking active sessions
    mock_results = MagicMock()
    mock_results.first.return_value = None
    mock_session.exec.return_value = mock_results

    # Set up the mock to return the expected game session after refresh
    async def mock_refresh(game_session):
        game_session.id = 1
        return None

    mock_session.refresh.side_effect = mock_refresh

    # Act
    result = await start_game_session(mock_session, user_id)

    # Assert
    mock_session.exec.assert_called_once()
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

    assert result.user_id == user_id
    assert result.id == 1
    assert result.status == GameSessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_start_game_session_existing(mock_session):
    """Test start_game_session when user already has an active game session."""
    # Arrange
    user_id = 1
    existing_game_session = GameSessionModel(
        id=1,
        user_id=user_id,
        status=GameSessionStatus.ACTIVE,
    )

    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = existing_game_session
    mock_session.exec.return_value = mock_results

    # Act
    result = await start_game_session(mock_session, user_id)

    # Assert
    mock_session.exec.assert_called_once()
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()

    assert result == existing_game_session


@pytest.mark.asyncio
async def test_stop_game_session_success(mock_session):
    """Test stop_game_session when game session exists and is active."""
    # Arrange
    user_id = 1
    game_session_id = 1

    # Create a mock game session
    game_session = GameSessionModel(
        id=game_session_id,
        user_id=user_id,
        status=GameSessionStatus.ACTIVE,
        start_time=get_utc_timestamp(),
    )

    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = game_session
    mock_session.exec.return_value = mock_results

    # Act
    with patch('dacodes_test.models.games.get_utc_timestamp') as mock_timestamp:
        # Mock the timestamp to be 15 seconds after start_time
        stop_time = get_utc_timestamp()
        mock_timestamp.return_value = stop_time

        result = await stop_game_session(mock_session, game_session_id, user_id)

    # Assert
    assert mock_session.exec.call_count == 1
    assert mock_session.add.call_count == 2  # Called twice in the function
    assert mock_session.commit.call_count == 2  # Called twice in the function
    assert mock_session.refresh.call_count == 2  # Called twice in the function

    assert result.id == game_session_id
    assert result.user_id == user_id
    assert result.status == GameSessionStatus.STOPPED
    assert result.stop_time == stop_time
    assert result.duration is not None
    assert result.deviation is not None


@pytest.mark.asyncio
async def test_stop_game_session_not_found(mock_session):
    """Test stop_game_session when game session does not exist."""
    # Arrange
    user_id = 1
    game_session_id = 999  # Non-existent ID

    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = None
    mock_session.exec.return_value = mock_results

    # Act
    result = await stop_game_session(mock_session, game_session_id, user_id)

    # Assert
    mock_session.exec.assert_called_once()
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()

    assert result is None


@pytest.mark.asyncio
async def test_calc_leaderboard(mock_session):
    """Test calc_leaderboard function."""
    # Arrange
    mock_results = [
        MagicMock(username="user1", total_games=5, avg_deviation=100.5, best_deviation=50.2),
        MagicMock(username="user2", total_games=3, avg_deviation=150.7, best_deviation=75.3),
    ]

    # Mock the session.execute().all() call
    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = mock_results
    mock_session.execute.return_value = mock_execute_result

    # Act
    result = await calc_leaderboard(mock_session)

    # Assert
    mock_session.execute.assert_called_once()

    assert len(result) == 2
    assert result[0]["username"] == "user1"
    assert result[0]["total_games"] == 5
    assert result[0]["average_deviation"] == 100.5
    assert result[0]["best_deviation"] == 50.2

    assert result[1]["username"] == "user2"
    assert result[1]["total_games"] == 3
    assert result[1]["average_deviation"] == 150.7
    assert result[1]["best_deviation"] == 75.3


@pytest.mark.asyncio
async def test_user_game_history_with_history(mock_session):
    """Test user_game_history when user has game history."""
    # Arrange
    user_id = 1

    # Mock the stats query result
    mock_stats = MagicMock(
        username="testuser",
        total_games=3,
        avg_deviation=120.5,
        best_deviation=60.2
    )

    # Mock the session.execute().first() call for stats
    mock_execute_result = MagicMock()
    mock_execute_result.first.return_value = mock_stats
    mock_session.execute.return_value = mock_execute_result

    # Mock the game history
    game_history = [
        GameSessionModel(id=1, user_id=user_id, status=GameSessionStatus.STOPPED),
        GameSessionModel(id=2, user_id=user_id, status=GameSessionStatus.STOPPED),
        GameSessionModel(id=3, user_id=user_id, status=GameSessionStatus.ACTIVE),
    ]

    # Mock the session.exec().all() call for game history
    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = game_history
    mock_session.exec.return_value = mock_exec_result

    # Mock the dict method for GameSessionModel
    with patch('dacodes_test.models.games.GameSessionModel.dict', 
               side_effect=lambda: {"id": 1, "user_id": user_id, "status": "stopped"}):

        # Act
        result = await user_game_history(mock_session, user_id)

    # Assert
    mock_session.execute.assert_called_once()
    mock_session.exec.assert_called_once()

    assert result["username"] == "testuser"
    assert result["total_games"] == 3
    assert result["average_deviation"] == 120.5
    assert result["best_deviation"] == 60.2
    assert len(result["history"]) == 3


@pytest.mark.asyncio
async def test_has_game_history_true(mock_session):
    """Test has_game_history when user has game history."""
    # Arrange
    user_id = 1
    game_history = [
        GameSessionModel(id=1, user_id=user_id),
        GameSessionModel(id=2, user_id=user_id),
    ]

    # Mock the query execution
    mock_results = MagicMock()
    mock_results.all.return_value = game_history
    mock_session.exec.return_value = mock_results

    # Act
    result = await has_game_history(mock_session, user_id)

    # Assert
    mock_session.exec.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_has_game_history_false(mock_session):
    """Test has_game_history when user has no game history."""
    # Arrange
    user_id = 1

    # Mock the query execution
    mock_results = MagicMock()
    mock_results.all.return_value = []
    mock_session.exec.return_value = mock_results

    # Act
    result = await has_game_history(mock_session, user_id)

    # Assert
    mock_session.exec.assert_called_once()
    assert result is False
