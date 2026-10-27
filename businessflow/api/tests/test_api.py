import os
import tempfile

from fastapi.testclient import TestClient


def test_crm_workflow():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_URL"] = f"sqlite:///{directory}/test.db"
        from importlib import reload
        import main
        reload(main)
        with TestClient(main.app) as client:
            assert client.get("/health").json() == {"status": "ok"}
            c = client.post("/api/clients", json={"name": "Ada", "company": "Orbit", "email": "ada@example.com"})
            assert c.status_code == 201
            cid = c.json()["id"]
            d = client.post("/api/deals", json={"name": "Website", "client_id": cid, "value": 1250})
            assert d.status_code == 201
            did = d.json()["id"]
            assert client.get("/api/metrics").json()["open_pipeline"] == 1250
            assert client.patch(f"/api/deals/{did}", json={"stage": "Won"}).status_code == 200
            assert client.get("/api/metrics").json()["closed_won"] == 1250
            t = client.post("/api/tasks", json={"title": "Follow up", "due": "Friday"})
            assert t.status_code == 201
            tid = t.json()["id"]
            assert client.patch(f"/api/tasks/{tid}", json={"done": True}).json()["done"] is True
            assert client.delete(f"/api/clients/{cid}").status_code == 409
            assert client.delete(f"/api/deals/{did}").status_code == 204
            assert client.delete(f"/api/clients/{cid}").status_code == 204
            assert client.delete(f"/api/tasks/{tid}").status_code == 204


def test_invalid_deal_value():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_URL"] = f"sqlite:///{directory}/test.db"
        from importlib import reload
        import main
        reload(main)
        with TestClient(main.app) as client:
            res = client.post("/api/deals", json={"name": "Bad", "client_id": 12, "value": -2})
            assert res.status_code == 422
