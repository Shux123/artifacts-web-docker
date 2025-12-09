# Artifacts Web — Flask + Docker Application

A Flask-based web application packaged in Docker, featuring PostgreSQL, Redis, Celery workers, and Telegram integration.  
This project demonstrates backend and DevOps skills in:

- Python & Flask  
- Celery task automation  
- Redis message broker  
- PostgreSQL database  
- Docker & Docker Compose  
- Environment-based configuration  
- Telegram Bot API integration  

It is suitable for including in a **CV / portfolio** as a real-world backend project.

---

## Features

- Flask web application with modular structure  
- Celery workers for background automation  
- Redis as a message broker  
- Docker Compose for multi-container orchestration  
- PostgreSQL database with persistent storage  
- Configurable Telegram bot notifications  
- Token-based protection for internal API access  
- Fully reproducible environment (development/production)

---

## Project Structure
```
artifacts-web-docker/
├── .env
├── .gitignore
├── artifacts.py
├── config.py
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
│
├── app/
│ ├── all_requests.py
│ ├── bot_tasks.py
│ ├── char_requests.py
│ ├── models.py
│ ├── telegram_bot.py
│ └── __init__.py
│
│ ├── char/
│ │ ├── forms.py
│ │ ├── views.py
│ │ └── __init__.py
│
│ ├── main/
│ │ ├── forms.py
│ │ ├── views.py
│ │ └── __init__.py
│
│ ├── static/
│ │ ├── script.js
│ │ ├── styles.css
│ │ └── images/
│ │   └── maps/
│
│ └── templates/
```

---

## Environment Variables (.env)
```.env
SECRET_KEY=
TELEGRAM_BOT_TOKEN=
ARTIFACTS_TOKEN=
TELEGRAM_BOT_CHAT_ID='chat number'
DATABASE_URL=postgresql://flask_user:'password'@db:5432/artifacts_db
POSTGRES_PASSWORD='password'
```

### Description

- **SECRET_KEY** — Flask secret key (security)  
- **TELEGRAM_BOT_TOKEN** — Telegram Bot API token  
- **ARTIFACTS_TOKEN** — Internal API access token  
- **TELEGRAM_BOT_CHAT_ID** — Telegram chat ID for notifications  
- **DATABASE_URL** — SQLAlchemy database connection URL  
- **POSTGRES_PASSWORD** — PostgreSQL container password  

---

## Docker Services

The `docker-compose.yml` defines:

- **web** — Flask application  
- **db** — PostgreSQL database  
- **redis** — Redis instance (Celery broker)  
- **worker** — Celery worker container  

Together they provide a full, production-like multi-service environment.

---

## Running the Application (Docker)

1. Clone the repository  
```bash
git clone https://github.com/Shux123/artifacts-web-docker
cd artifacts-web-docker
```
2. Create a `.env` file with required variables.
3. Build and start all services:
```bash
docker-compose up --build
```
The application will be available at:
```
http://localhost:8000
```

4. Stop services
```bash
docker-compose down
```

---

## Initializing the Database
Run the following command to initialize tables:
```bash
docker-compose run --rm web flask --app artifacts init-db
```
This creates all necessary tables in the PostgreSQL database.

---

## Celery & Redis
- The project uses Celery for background / asynchronous tasks.
- Redis serves as the Celery message broker.
- Running docker-compose up starts the Celery worker automatically.

Typical uses of Celery in this project:
- Background automation
- Scheduled tasks (via Celery Beat)
- Integration with external APIs (e.g. artifacts API)
- Sending Telegram notifications asynchronously

This design keeps the web application responsive while heavy/long tasks run in background.

---

## Purpose of the Project
This project was built to:
- Practice building Flask web applications
- Learn Docker Compose orchestration for multi-container services
- Use Celery + Redis for asynchronous and scheduled tasks
- Work with PostgreSQL via SQLAlchemy
- Integrate external services (Telegram Bot API)
- Provide a real-world backend project for portfolio / CV

## Author
**Artem Danylchuk**
Email: **shuxart@gmail.com**
GitHub: https://github.com/Shux123

