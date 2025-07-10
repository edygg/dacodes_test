import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException, status

from main import app
from dacodes_test.auth.jwt import create_access_token
from dacodes_test.models import get_session
from dacodes_test.models.users import UserModel
from dacodes_test.models.games import GameSessionModel, GameSessionStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_user():
    """Create a test user."""
    return UserModel(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )


@pytest.fixture
def auth_token(client):
    """Get a real authentication token for testing."""
    # Login with one of the test users
    response = client.post(
        "/auth/login",
        data={
            "username": "edygg_1",
            "password": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Check that the login was successful
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Return the token
    return data["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers with the auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_get_session():
    """Create a mock session for testing."""
    # We'll use a simpler approach - just patch the specific functions that are called
    # This fixture is kept for compatibility with existing tests
    session = AsyncMock()

    # Setup the dependency override
    app.dependency_overrides = {}  # Clear any existing overrides

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    yield session

    # Clean up
    app.dependency_overrides = {}

@pytest.fixture
def mock_auth_dependencies(test_user):
    """Override authentication dependencies for testing."""
    # Setup the dependency override
    app.dependency_overrides = {}  # Clear any existing overrides

    # Import the dependencies we need to override
    from dacodes_test.auth.jwt import CurrentUserDep

    # Override the CurrentUserDep dependency directly
    # This is the key change - we're bypassing the entire auth chain
    app.dependency_overrides[CurrentUserDep] = lambda: test_user

    yield

    # Clean up
    app.dependency_overrides = {}


# Test health check endpoint
def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Test register endpoint
def test_register_user(client, mock_get_session):
    """Test user registration endpoint."""
    with patch("dacodes_test.models.users.create_user") as mock_create_user:
        # Configure the mock to return a user
        user_model = UserModel(
            id=1,
            username="newuser",
            email="new@example.com",
            password_hash="hashed_password"
        )

        # For async functions, we need to use side_effect with an async function
        async def mock_create_user_side_effect(*args, **kwargs):
            return user_model

        mock_create_user.side_effect = mock_create_user_side_effect

        # Test successful registration
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

        # Test invalid input
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                # Missing email and password
            }
        )

        assert response.status_code == 422  # Validation error


# Test login endpoint
def test_login_user(client, test_user):
    """Test user login endpoint."""
    # Patch the authenticate_user function directly
    with patch("main.authenticate_user") as mock_authenticate:
        # Configure the mock for successful login
        mock_authenticate.return_value = test_user

        # Test successful login
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "password123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Configure the mock for failed login
        mock_authenticate.return_value = None

        # Test invalid credentials
        response = client.post(
            "/auth/login",
            data={
                "username": "wronguser",
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Incorrect username or password"


# Test start game endpoint
def test_start_game(client, auth_headers):
    """Test game start endpoint."""
    # Test successful game start with real authentication
    response = client.post("/games/start", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert data["status"] == GameSessionStatus.ACTIVE

    # Test unauthorized access
    response = client.post("/games/start")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


# Test stop game endpoint
def test_stop_game(client, auth_headers):
    """Test game stop endpoint."""
    # First, start a game session
    start_response = client.post("/games/start", headers=auth_headers)
    assert start_response.status_code == 200
    start_data = start_response.json()
    game_session_id = start_data["id"]

    # Test successful game stop with real authentication
    response = client.post(f"/games/{game_session_id}/stop", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert data["status"] == GameSessionStatus.STOPPED

    # Test game session not found
    response = client.post(f"/games/999/stop", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

    # Test unauthorized access
    response = client.post(f"/games/{game_session_id}/stop")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


# Test leaderboard endpoint
def test_get_leaderboard(client):
    """Test leaderboard endpoint."""
    # Patch the function directly
    with patch("dacodes_test.models.games.calc_leaderboard") as mock_calc_leaderboard:
        # Configure the mock for default pagination
        mock_calc_leaderboard.return_value = [
            {
                "username": "user1",
                "total_games": 5,
                "average_deviation": 100.5,
                "best_deviation": 50.2
            },
            {
                "username": "user2",
                "total_games": 3,
                "average_deviation": 150.7,
                "best_deviation": 75.3
            }
        ]

        # Test default pagination
        response = client.get("/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "username" in data[0]
        assert "total_games" in data[0]
        assert "average_deviation" in data[0]
        assert "best_deviation" in data[0]

        # Configure the mock for custom pagination
        mock_calc_leaderboard.return_value = [
            {
                "username": "user3",
                "total_games": 2,
                "average_deviation": 200.1,
                "best_deviation": 100.0
            }
        ]

        # Test custom pagination
        response = client.get("/leaderboard?page=2&per_page=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


# Test user game history endpoint
def test_get_user_game_history_success(client):
    """Test getting user game history successfully."""
    user_id = 1

    # Patch the functions directly
    with patch("dacodes_test.models.users.get_user_by_id") as mock_get_user_by_id, \
         patch("dacodes_test.models.games.has_game_history") as mock_has_game_history, \
         patch("dacodes_test.models.games.user_game_history") as mock_user_game_history:

        # Configure the mocks
        mock_get_user_by_id.return_value = UserModel(
            id=user_id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        mock_has_game_history.return_value = True
        mock_user_game_history.return_value = {
            "username": "testuser",
            "total_games": 3,
            "average_deviation": 120.5,
            "best_deviation": 60.2,
            "history": [
                {"id": 1, "user_id": user_id, "status": "stopped"},
                {"id": 2, "user_id": user_id, "status": "stopped"},
                {"id": 3, "user_id": user_id, "status": "active"}
            ]
        }

        response = client.get(f"/analytics/user/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["total_games"] == 3
    assert data["average_deviation"] == 120.5
    assert data["best_deviation"] == 60.2
    assert len(data["history"]) == 3


def test_get_user_game_history_user_not_found(client):
    """Test getting game history for non-existent user."""
    user_id = 999

    # Patch the function directly
    with patch("dacodes_test.models.users.get_user_by_id") as mock_get_user_by_id:
        # Configure the mock
        mock_get_user_by_id.return_value = None

        response = client.get(f"/analytics/user/{user_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "No user found."


def test_get_user_game_history_no_games(client):
    """Test getting game history for user with no games."""
    user_id = 1

    # Patch the functions directly
    with patch("dacodes_test.models.users.get_user_by_id") as mock_get_user_by_id, \
         patch("dacodes_test.models.games.has_game_history") as mock_has_game_history:

        # Configure the mocks
        mock_get_user_by_id.return_value = UserModel(
            id=user_id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        mock_has_game_history.return_value = False

        response = client.get(f"/analytics/user/{user_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "No games found."
