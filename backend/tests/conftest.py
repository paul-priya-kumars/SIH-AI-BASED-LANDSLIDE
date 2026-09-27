import pytest
from app.database import init_db

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Initialize the database with demo data before running tests."""
    init_db()