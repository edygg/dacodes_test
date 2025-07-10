# Time It Right Game API

This repository contains a FastAPI application for a game called "Time It Right" where players try to stop a timer as close as possible to 10 seconds.

## Running the Project with Docker Compose

To run the project using Docker Compose, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.
2. Clone this repository to your local machine.
3. Navigate to the project directory.
4. Run the following command to start the application:

```bash
docker-compose up
```

This will build the Docker image and start the API service. The API will be available at http://localhost:8000.

## Running Tests with Docker Compose

To run the tests using Docker Compose, use the following command:

```bash
docker-compose run api pytest
```

This will run all the tests in the `tests` directory. You can also run specific test files or test functions:

```bash
# Run a specific test file
docker-compose run api pytest tests/test_api.py

# Run a specific test function
docker-compose run api pytest tests/test_api.py::test_health_check
```

## Accessing Swagger Documentation

The API includes Swagger documentation which can be accessed at:

```
http://localhost:8000/docs/
```

This interactive documentation allows you to:
- View all available endpoints
- See request and response schemas
- Test the API directly from the browser

## Key Functions

### calc_leaderboard

The `calc_leaderboard` function calculates and returns a leaderboard of users based on their game performance. It:

1. Takes a database session, page number, and items per page as parameters
2. Calculates the following statistics for each user:
   - Total number of completed games
   - Average deviation from the target time (10 seconds)
   - Best (lowest) deviation achieved
3. Orders users by their average deviation (ascending, so better performers appear first)
4. Applies pagination to the results
5. Returns a list of users with their statistics

This function is used by the `/leaderboard` endpoint to show the best performers in the game.

### user_game_history

The `user_game_history` function retrieves a specific user's game statistics and history. It:

1. Takes a database session and user_id as parameters
2. Calculates the same statistics as in the leaderboard (total games, average deviation, best deviation)
3. Retrieves all game sessions for the user (both active and completed)
4. Returns a dictionary containing:
   - Username
   - Game statistics (total games, average deviation, best deviation)
   - Complete history of all game sessions

This function is used by the `/analytics/user/{user_id}` endpoint to show detailed information about a specific user's performance and game history.

## Game Mechanics

In the "Time It Right" game:
1. Users start a game session with the `/games/start` endpoint
2. They try to stop the session after exactly 10 seconds using the `/games/{game_session_id}/stop` endpoint
3. The system calculates how close they were to the 10-second target (the "deviation")
4. Lower deviation scores are better (meaning the player was closer to exactly 10 seconds)
5. Players can compare their performance on the leaderboard