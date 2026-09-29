import os, tempfile, pytest
from app.app import create_app
from app.db import init_db, seed_db

@pytest.fixture()
def client():
    fd,path=tempfile.mkstemp(suffix=".db"); os.close(fd)
    app=create_app(".dogfood.toml")
    app.config.update(TESTING=True,DATABASE_URL=path,SECRET_KEY="test")
    with app.app_context():
        init_db(); seed_db()
    with app.test_client() as c:
        yield c
    os.remove(path)

def login(c,email,password):
    return c.post("/api/login",json={"email":email,"password":password})

def test_seeded_portal(client):
    r=client.get("/")
    assert r.status_code==200
    assert b"HackForge Dogfood 2026" in r.data

def test_judge_isolation(client):
    login(client,"judge1@example.com","judge123")
    r=client.get("/api/judge/scores/999999")
    assert r.status_code in (200,403)

    login(client,"judge2@example.com","judge123")
    r=client.get("/api/judge/scores/1")
    assert r.status_code==403

def test_registration(client):
    r=client.post("/api/register",json={
        "name":"New User","email":"new@example.com","password":"pass123"})
    assert r.status_code==201

def test_participant_cannot_export(client):
    login(client,"alice@example.com","alice123")
    assert client.get("/api/export/submissions.csv").status_code==403
