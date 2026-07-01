def test_register_user(client):
    response = client.post("/register", json={
        "username": "jamshid",
        "password": "12345678",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "jamshid"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicated_user(client):
    client.post("/register", json={"username": "jamshid", "password": "12345678"})
    response =client.post("/register", json={
            "username": "jamshid","password": "12345678"
        })
    assert response.status_code == 400
    assert "detail" in response.json()


def test_login_returns_token(client):
    client.post("/register", json={"username": "jamshid", "password": "12345678"})

    response = client.post("/token", data={
        "username":"jamshid","password":"12345678"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_users_me_with_token(client):
    client.post("/register", json={"username": "jamshid", "password": "12345678"})
    response = client.post("/token", data={"username": "jamshid", "password": "12345678"})
    token = response.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "jamshid"

