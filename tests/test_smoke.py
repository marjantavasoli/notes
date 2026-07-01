import pytest

def test_unauthenticated_notes_returns_401(client):
    response = client.get("/notes")
    assert response.status_code == 401



