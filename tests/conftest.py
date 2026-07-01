import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from main import app
from database import get_session
import models

# In-memory SQLite — fast, isolated, disappears when tests ends
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Async fixture #1: a fresh engine for each tests
@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    # Cleanup after tests
    await engine.dispose()


# Async fixture #2: a sessionmaker tied to the tests engine
@pytest_asyncio.fixture
async def test_session_maker(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


# Regular fixture: the tests client, with database swapped
@pytest.fixture
def client(test_session_maker):
    # This is the FUNCTION that will replace get_session during tests
    async def override_get_session():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    # Hand the tests client to the tests
    with TestClient(app) as c:
        yield c

    # After tests: undo the override so other tests start clean
    app.dependency_overrides.clear()



@pytest.fixture
def jamshid_credentials():
    return {"username": "jamshid", "password": "12345678"}


@pytest.fixture
def bob_credentials():
    return {"username": "bob", "password": "12345678"}


@pytest.fixture
def jamshid_token(client, jamshid_credentials):
    """Register alice and return her access token."""
    client.post("/register", json=jamshid_credentials)
    response = client.post("/token", data=jamshid_credentials)
    return response.json()["access_token"]


@pytest.fixture
def bob_token(client, bob_credentials):
    """Register bob and return his access token."""
    client.post("/register", json=bob_credentials)
    response = client.post("/token", data=bob_credentials)
    return response.json()["access_token"]


@pytest.fixture
def jamshid_headers(jamshid_token):
    """Authorization header for alice."""
    return {"Authorization": f"Bearer {jamshid_token}"}


@pytest.fixture
def bob_headers(bob_token):
    """Authorization header for bob."""
    return {"Authorization": f"Bearer {bob_token}"}