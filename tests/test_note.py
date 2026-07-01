def test_create_note(client, jamshid_headers):
    response = client.post(
        "/notes",
        json={"title": "first note"},
        headers=jamshid_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "first note"
    assert "id" in data


def test_get_notes(client, jamshid_headers):
    client.post(
        "/notes",json={"title": "first note"},
        headers=jamshid_headers, )
    client.post("/notes/",json={"title": "second note"},headers=jamshid_headers)

    response = client.get("/notes/",headers=jamshid_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


def test_get_note_by_id(client, jamshid_headers,bob_headers):
    response = client.post("/notes/",json={"title": "first note"},headers=jamshid_headers)
    data_1 = response.json()
    id = data_1["id"]
    response = client.get(f"/notes/{id}",headers=jamshid_headers)
    assert response.status_code == 200
    data_2 = response.json()
    assert data_2["title"] == "first note"
    response = client.post(f"/notes/",json={"title":"bob's note"},headers=bob_headers)
    data_3 = response.json()
    id_bob = data_3["id"]
    response = client.get(f"/notes/{id_bob}",headers=jamshid_headers)
    assert response.status_code == 403


def test_get_nonexistent_note(client, jamshid_headers):
    response = client.get(f"/notes/{999}",headers=jamshid_headers)
    assert response.status_code == 404

def test_delete_own_note(client, jamshid_headers):
    response = client.post(
        "/notes/",json={"title": "first note"},headers=jamshid_headers,
    )
    data = response.json()
    id = data["id"]
    response = client.delete(f"/notes/{id}",headers=jamshid_headers)
    assert response.status_code == 200
    response = client.delete(f"/notes/{999}",headers=jamshid_headers)
    assert response.status_code == 404

def test_delete_other_note(client,bob_headers, jamshid_headers):
    response = client.post("/notes/",json={"title": "first note"},headers=jamshid_headers)
    data = response.json()
    id = data["id"]
    response = client.delete(f"/notes/{id}",headers=bob_headers)
    assert response.status_code in (403,404)


def test_updated_at_changes_on_patch(client, jamshid_headers):
    create_response = client.post(
        "/notes/", json={"title": "note"}, headers=jamshid_headers
    )
    original_updated_at = create_response.json()["updated_at"]

    patch_response = client.patch(
        f"/notes/{create_response.json()['id']}",
        json={"title": "updated"},
        headers=jamshid_headers,
    )
    new_updated_at = patch_response.json()["updated_at"]

    assert new_updated_at != original_updated_at
