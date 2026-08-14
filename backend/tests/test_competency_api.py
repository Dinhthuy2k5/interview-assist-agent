def test_create_framework_with_criteria(client):
    payload = {
        "name": "Backend Engineer",
        "description": "Khung năng lực cho vị trí Backend Engineer",
        "criteria": [
            {"name": "Problem Solving", "weight": 1.5, "scoring_rubric": "1-5: ..."},
            {"name": "System Design", "weight": 1.0, "scoring_rubric": "1-5: ..."},
        ],
    }
    response = client.post("/frameworks", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Backend Engineer"
    assert len(body["criteria"]) == 2
    assert body["criteria"][0]["name"] == "Problem Solving"


def test_list_frameworks(client):
    client.post("/frameworks", json={"name": "FW1", "criteria": []})
    client.post("/frameworks", json={"name": "FW2", "criteria": []})
    response = client.get("/frameworks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_framework_not_found_returns_404(client):
    response = client.get("/frameworks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_framework_name(client):
    created = client.post("/frameworks", json={"name": "Old name", "criteria": []}).json()
    response = client.patch(f"/frameworks/{created['id']}", json={"name": "New name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New name"


def test_delete_framework(client):
    created = client.post("/frameworks", json={"name": "To delete", "criteria": []}).json()
    response = client.delete(f"/frameworks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/frameworks/{created['id']}").status_code == 404