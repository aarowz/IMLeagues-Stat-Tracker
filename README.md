# IMLeagues Stat Tracker

Built by Aaron Zhou, Ahaan Kallat, Lucas Chen, Timothy Matten, and Caleb Lys

This is the IMLeagues Stat Tracker project repository for tracking intramural sports statistics. The application provides comprehensive stat tracking, game management, and analytics for intramural sports leagues.

## Video Link

https://drive.google.com/file/d/1q9QAq8wzJfOI2VTWhWg9hKW4etUOXKd-/view?usp=sharing

## Overview

IMLeagues Stat Tracker is a full-stack web application designed to manage and track statistics for intramural sports leagues. The system supports four distinct user personas: Stat Keepers, Players, Team Captains, and System Administrators, each with role-specific functionality and access controls.

## Tech Stack

### Frontend

- Streamlit: Python-based framework for rapid UI development
- Plotly & Matplotlib: Advanced data visualization and charting
- Pandas: Data manipulation and analysis

### Backend

- Flask: Lightweight web framework for API development
- Flask-RESTful: REST API extensions for robust endpoint design
- MySQL: Relational database management system

### DevOps & Infrastructure

- Docker: Containerization for consistent deployment
- Docker Compose: Orchestration of multi-container applications

## Key Features

- Role-Based Access Control (RBAC): Tailored user experiences based on roles
- Real-Time Stat Entry: Live game statistics tracking during matches
- Comprehensive Analytics: Player and team performance analysis
- Game Management: Schedule, track, and finalize games
- Data Management: Administrative tools for system maintenance
- Awards System: Track and manage player achievements

## Repository Structure

- `app/` - Streamlit frontend application
  - `src/` - Source code
    - `Home.py` - Landing page with user role selection
    - `pages/` - Individual feature pages organized by role
- `api/` - Flask REST API backend
  - `backend/` - API route blueprints organized by persona
    - `stat_keeper/` - Stat Keeper routes
    - `player/` - Player routes
    - `team_captain/` - Team Captain routes
    - `system_admin/` - System Administrator routes
  - `.env` - Environment variables (create this file - see Environment Setup)
- `database-files/` - SQL scripts for database initialization
  - Files are executed in alphabetical order when the database container is first created
  - `01_imleagues_schema.sql` - Database schema (DDL)
  - `02_imleagues_data.sql` through `16_player_awards.sql` - Sample data (DML)
- `docker-compose.yaml` - Docker Compose configuration for all services

## Environment Setup

Before starting the application, you need to create a `.env` file in the `api/` directory with the following variables:

```bash
# Database Configuration
DB_USER=root
MYSQL_ROOT_PASSWORD=your_secure_password_here
DB_HOST=db
DB_PORT=3306
DB_NAME=im_league_tracker

# Flask Secret Key
SECRET_KEY=your_secret_key_here
```

**Important:** Replace `your_secure_password_here` and `your_secret_key_here` with your own secure values. The `.env` file is used by Docker Compose to configure the MySQL database container.

## Docker Deployment

### Prerequisites

1. Ensure Docker and Docker Compose are installed
2. Create the `.env` file in `api/` directory (see Environment Setup above)

### Starting the Application

To start all services (frontend, API, and database):

```bash
docker compose up -d
```

This command will:

- Build and start the Streamlit frontend (available at `http://localhost:8501`)
- Build and start the Flask API (available at `http://localhost:4000`)
- Create and initialize the MySQL database container
- Automatically execute all SQL files in `database-files/` in alphabetical order

### Viewing Logs

```bash
# View all logs
docker compose logs -f

# View logs for a specific service
docker compose logs -f app    # Frontend
docker compose logs -f api     # Backend API
docker compose logs -f db      # Database
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker compose down

# Stop and remove volumes (fresh start - will re-run SQL files)
docker compose down -v
```

### Service URLs

- Frontend (Streamlit): `http://localhost:8501`
- Backend API: `http://localhost:4000`
- MySQL Database: `localhost:3200` (external port) / `db:3306` (internal container port)
  - **Note**: MySQL is a database server, not an HTTP server. Connect using MySQL client tools (e.g., `mysql -h localhost -P 3200 -u root -p`), not via web browser

## API Overview

The REST API is organized into 4 Flask Blueprints, each corresponding to a user persona. **All API endpoints are prefixed with their respective blueprint path.**

### Blueprint Structure

- **Stat Keeper** (`/stat-keeper`) - Game assignment, live stat entry, game finalization
- **Player** (`/player`) - Personal stats, game schedules, team/league exploration
- **Team Captain** (`/team-captain`) - Team management, game scheduling, performance tracking
- **System Administrator** (`/system-admin`) - System-wide analytics, data management, awards

### Endpoint Examples

All endpoints include the blueprint prefix. For example:

- `GET /player/players` - Get all players
- `GET /team-captain/teams/<team_id>/games` - Get games for a team
- `GET /stat-keeper/games/<game_id>` - Get game details
- `POST /stat-keeper/games/<game_id>/stat-events` - Create a stat event
- `PUT /team-captain/games` - Update game information
- `DELETE /stat-keeper/games/<game_id>/stat-events/<event_id>` - Delete a stat event

### API Details

- **Base URL**: `http://localhost:4000` (when running via Docker)
- **Response Format**: All endpoints return JSON
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Testing**: Use tools like `curl`, Postman, or your browser to test GET endpoints

### Example Request

```bash
# Get all players
curl http://localhost:4000/player/players

# Get games for team ID 1
curl http://localhost:4000/team-captain/teams/1/games
```

## Pages Organization

The pages are organized by Role using numerical prefixes to control their order in the Streamlit sidebar. Pages that start with a `0` are related to the Stat Keeper role. Pages that start with a `1` are related to the Player role or Team Captain role. Pages that start with a `2` are related to the System Administrator role.

Streamlit automatically discovers and orders pages alphanumerically by filename. For more information about how Streamlit's multi-page apps work, see the [official Streamlit documentation](https://docs.streamlit.io/library/get-started/multipage-apps).

## Local Development Setup

### Backend Setup

```bash
cd api
python backend_app.py
```

API runs on `http://localhost:4000`

### Frontend Setup

```bash
cd app/src
streamlit run Home.py
```

UI runs on `http://localhost:8501`

### Database Setup

- Configure MySQL connection in `api/.env`
- Initialize schema from `database-files/` SQL scripts

## Database Management

If you make changes to any SQL files in the `database-files/` folder after the database container is created, you'll need to delete and recreate the container for the changes to take effect. Simply stopping and restarting the container will not re-run the SQL files.

To recreate the database with updated SQL files:

```bash
docker compose down db -v
docker compose up db -d
```

The `-v` flag removes the volume associated with MySQL, which is necessary to rerun the SQL files.
