# IMLeagues Stat Tracker
built by Lucas Chen, Timothy Matten, Aaron Zhou and Caleb Lys

This is the IMLeagues Stat Tracker project repository for tracking intramural sports statistics. 

It includes most of the infrastructure setup (containers), sample databases, and example UI pages. 

# Video Link

https://drive.google.com/file/d/1q9QAq8wzJfOI2VTWhWg9hKW4etUOXKd-/view?usp=sharing

# Frontend
- Streamlit: Python-based framework for rapid UI development
- Plotly & Matplotlib: Advanced data visualization and charting
- Pandas: Data manipulation and analysis
- Scikit-learn & SHAP: Machine learning capabilities with model interpretability

# Backend
- Flask: Lightweight web framework for API development
- Flask-RESTful: REST API extensions for robust endpoint design
- MySQL: Relational database management system

# DevOps & Infrastructure
- Docker: Containerization for consistent deployment
- Docker Compose: Orchestration of multi-container applications

# Structure of the Repo

- This repository is organized into five main directories:
  - `./app` - the Streamlit app
  - `./api` - the Flask REST API
  - `./database-files` - SQL scripts to initialize the MySQL database
  - `./datasets` - folder for storing datasets

- The repo also contains a `docker-compose.yaml` file that is used to set up the Docker containers for the front end app, the REST API, and MySQL database. 

# Key Features

- Role-Based Access Control (RBAC): Tailored user experiences based on roles
-Real-Time Stat Entry: Live game statistics tracking during matches
- Comprehensive Analytics: Player and team performance analysis
- Game Management: Schedule, track, and finalize games
- Data Management: Administrative tools for system maintenance
- Awards System: Track and manage player achievements

# Pages
The pages are organized by Role using numerical prefixes to control their order in the Streamlit sidebar. Pages that start with a `0` are related to the Stat Keeper role. Pages that start with a `1` are related to the Player role or Team Captain role. Pages that start with a `2` are related to the System Administrator role.

Streamlit automatically discovers and orders pages alphanumerically by filename. For more information about how Streamlit's multi-page apps work, see the [official Streamlit documentation](https://docs.streamlit.io/library/get-started/multipage-apps).

# Local Development Setup

1. Backend Setup:
   \`\`\`bash
   cd api
   python backend_app.py
   API runs on http://localhost:4000
   \`\`\`

2. Frontend Setup:
   \`\`\`bash
   cd app/src
   streamlit run Home.py
   UI runs on http://localhost:8501
   \`\`\`

3. Database Setup:
   - Configure MySQL connection in \`api/.env\`
   - Initialize schema from \`database-files/\` SQL scripts

# Docker Deployment

\`\`\`bash
# Start all services
docker-compose up --build

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Clean up volumes (fresh start)
docker-compose down -v
\`\`\`

Service Mappings:
- Frontend: \`http://localhost:8501\`
- Backend API: \`http://localhost:4000\`
- MySQL Database: \`localhost:3200\`
