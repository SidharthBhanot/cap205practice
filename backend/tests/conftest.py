import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.seed_data import seed_database


@pytest.fixture
def app(tmp_path):
    return create_app(f"sqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def seeded(client, app):
    with app.state.session_factory() as db:
        seed_database(db)
    return client
