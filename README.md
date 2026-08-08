# K Dynamics Business Management System

This is an offline desktop application for K Dynamics (PRIVATE) LIMITED and RN Scanner and Digital Print House.

## Project Structure

- `assets/`: Contains application assets (images, logos).
- `config/`: Configuration settings and environment variables.
- `database/`: Database connection and session management.
- `models/`: SQLAlchemy ORM models.
- `services/`: Business logic and data access layer (to be implemented).
- `ui/`: PySide6 frontend views and components.
- `utils/`: Helper functions and application logger.

## Technology Stack

- **Python 3.x**
- **PySide6**: UI framework (Qt for Python).
- **SQLite**: Database.
- **SQLAlchemy**: Object Relational Mapper.
- **Alembic**: Database migrations.

## Installation

1. Clone or download this project.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Execute the `main.py` file to launch the application:
```bash
python main.py
```

## Database Migrations

This project uses Alembic for database migrations.

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "migration message"
```

To apply migrations to the database:
```bash
alembic upgrade head
```
