import pytest
from unittest.mock import AsyncMock, MagicMock

from dacodes_test.models.users import (
    UserModel,
    get_user_by_username,
    create_user,
    get_user_by_id,
    get_user_password_hash,
)
from dacodes_test.payloads.users import UserCreate


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_user_by_username_found(mock_session):
    """Test get_user_by_username when user is found."""
    # Arrange
    username = "test_user"
    expected_user = UserModel(
        id=1,
        username=username,
        email="test@example.com",
        password_hash=get_user_password_hash("password"),
    )
    
    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = expected_user
    mock_session.exec.return_value = mock_results
    
    # Act
    result = await get_user_by_username(mock_session, username)
    
    # Assert
    mock_session.exec.assert_called_once()
    assert result == expected_user
    assert result.username == username


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(mock_session):
    """Test get_user_by_username when user is not found."""
    # Arrange
    username = "nonexistent_user"
    
    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = None
    mock_session.exec.return_value = mock_results
    
    # Act
    result = await get_user_by_username(mock_session, username)
    
    # Assert
    mock_session.exec.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_create_user(mock_session):
    """Test create_user function."""
    # Arrange
    user_data = UserCreate(
        username="new_user",
        email="new@example.com",
        password="secure_password",
    )
    
    # Mock the user model that would be created
    expected_user = UserModel(
        id=1,
        username=user_data.username,
        email=user_data.email,
        password_hash=get_user_password_hash(user_data.password),
    )
    
    # Set up the mock to return the expected user after refresh
    async def mock_refresh(user_model):
        user_model.id = 1
        return None
    
    mock_session.refresh.side_effect = mock_refresh
    
    # Act
    result = await create_user(mock_session, user_data)
    
    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    assert result.username == user_data.username
    assert result.email == user_data.email
    assert result.id == 1  # Should be set by the mock refresh


@pytest.mark.asyncio
async def test_get_user_by_id_found(mock_session):
    """Test get_user_by_id when user is found."""
    # Arrange
    user_id = 1
    expected_user = UserModel(
        id=user_id,
        username="test_user",
        email="test@example.com",
        password_hash=get_user_password_hash("password"),
    )
    
    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = expected_user
    mock_session.exec.return_value = mock_results
    
    # Act
    result = await get_user_by_id(mock_session, user_id)
    
    # Assert
    mock_session.exec.assert_called_once()
    assert result == expected_user
    assert result.id == user_id


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mock_session):
    """Test get_user_by_id when user is not found."""
    # Arrange
    user_id = 999  # Non-existent ID
    
    # Mock the query execution
    mock_results = MagicMock()
    mock_results.first.return_value = None
    mock_session.exec.return_value = mock_results
    
    # Act
    result = await get_user_by_id(mock_session, user_id)
    
    # Assert
    mock_session.exec.assert_called_once()
    assert result is None