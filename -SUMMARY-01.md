# Technical Stack Summary — AP Automation Core Engine

## Core Stack
- **Python 3.11+** with FastAPI
- **PostgreSQL 15+** with async SQLAlchemy 2.0
- **Alembic** for database migrations
- **Pydantic v2** for data validation
- **Docker** + docker-compose for deployment

## Authentication
- JWT (HS256) for API authentication
- bcrypt for password hashing

## API Design
- RESTful with `/api/v1/` versioning
- Pydantic schemas for request/response validation
- Auto-generated OpenAPI docs

## Project Structure
