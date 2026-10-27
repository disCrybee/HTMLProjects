import os
import tempfile
from importlib import reload

from fastapi.testclient import TestClient


def make_client(directory):
    os.environ["DATABASE_URL"] = f"sqlite:///{directory}/test.db"
    os.environ["BUSINESSFLOW_SESSION_SECRET"] = "test-session-secret-at-least-32-characters"
    import main
    reload(main)
    return TestClient(main.app)


def register(client, email):
    response = client.post("/auth/register", json={"email": email, "password": "a-strong-test-password"})
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_crm_workflow():
    with tempfile.TemporaryDirectory() as directory:
        with make_client(directory) as client:
            assert client.get("/health").json() == {"status": "ok"}
            headers = register(client, "ada@example.com")
            c = client.post("/api/clients", json={"name": "Ada", "company": "Orbit", "email": "ada@example.com"}, headers=headers)
            assert c.status_code == 201, c.text
            cid = c.json()["id"]
            d = client.post("/api/deals", json={"name": "Website", "client_id": cid, "value": 1250}, headers=headers)
            assert d.status_code == 201, d.text
            did = d.json()["id"]
            assert client.get("/api/metrics", headers=headers).json()["open_pipeline"] == 1250
            assert client.patch(f"/api/deals/{did}", json={"stage": "Won"}, headers=headers).status_code == 200
            assert client.get("/api/metrics", headers=headers).json()["closed_won"] == 1250
            t = client.post("/api/tasks", json={"title": "Follow up", "due": "Friday"}, headers=headers)
            assert t.status_code == 201
            tid = t.json()["id"]
            assert client.patch(f"/api/tasks/{tid}", json={"done": True}, headers=headers).json()["done"] is True
            assert client.delete(f"/api/clients/{cid}", headers=headers).status_code == 409
            assert client.delete(f"/api/deals/{did}", headers=headers).status_code == 204
            assert client.delete(f"/api/clients/{cid}", headers=headers).status_code == 204
            assert client.delete(f"/api/tasks/{tid}", headers=headers).status_code == 204


def test_account_isolation():
    with tempfile.TemporaryDirectory() as directory:
        with make_client(directory) as client:
            first = register(client, "first@example.com")
            second = register(client, "second@example.com")
            assert client.get("/api/clients").status_code == 401
            assert client.get("/auth/me", headers=first).json()["email"] == "first@example.com"
            a = client.post("/api/clients", json={"name": "First", "company": "A", "email": "first@example.com"}, headers=first)
            cid = a.json()["id"]
            assert client.get("/api/clients", headers=second).json() == []
            assert client.delete(f"/api/clients/{cid}", headers=second).status_code == 404
            assert client.post("/api/deals", json={"name": "Not allowed", "client_id": cid, "value": 100}, headers=second).status_code == 404
            assert client.get("/api/metrics", headers=second).json()["clients"] == 0
            assert client.post("/auth/login", json={"email": "first@example.com", "password": "wrong-password"}).status_code == 401
            assert client.post("/auth/login", json={"email": "first@example.com", "password": "a-strong-test-password"}).status_code == 200


def test_validation():
    with tempfile.TemporaryDirectory() as directory:
        with make_client(directory) as client:
            headers = register(client, "test@example.com")
            res = client.post("/api/deals", json={"name": "Bad", "client_id": 12, "value": -2}, headers=headers)
            assert res.status_code == 422
            assert client.post("/auth/register", json={"email": "test@example.com", "password": "a-strong-test-password"}).status_code == 409


def test_cannot_change_other_users_deals_or_tasks():
    with tempfile.TemporaryDirectory() as directory:
        with make_client(directory) as client:
            first = register(client, "owner@example.com")
            second = register(client, "other@example.com")
            c = client.post("/api/clients", headers=first, json={"name": "Owner", "company": "Own Co", "email": "owner@example.com"})
            cid = c.json()["id"]
            d = client.post("/api/deals", headers=first, json={"name": "Private deal", "client_id": cid, "value": 450})
            t = client.post("/api/tasks", headers=first, json={"title": "Private task", "due": "Next week"})
            did, tid = d.json()["id"], t.json()["id"]
            assert client.get("/api/deals", headers=second).json() == []
            assert client.get("/api/tasks", headers=second).json() == []
            assert client.patch(f"/api/deals/{did}", headers=second, json={"stage": "Won"}).status_code == 404
            assert client.delete(f"/api/deals/{did}", headers=second).status_code == 404
            assert client.patch(f"/api/tasks/{tid}", headers=second, json={"done": True}).status_code == 404
            assert client.delete(f"/api/tasks/{tid}", headers=second).status_code == 404
            assert client.get("/api/metrics", headers=second).json()["open_pipeline"] == 0
            assert client.get("/api/deals", headers=first).json()[0]["stage"] == "Lead"
            assert client.get("/api/tasks", headers=first).json()[0]["done"] is False
