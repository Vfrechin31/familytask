import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session


@pytest.fixture(name="session")
def session_fixture():
    # Base SQLite en mémoire, propre à chaque test
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_signup_create_task_and_list(client):
    signup_response = client.post(
        "/api/signup",
        json={
            "email": "test@example.com",
            "password": "motdepasse123",
            "name": "Testeur",
            "family": "Famille Test",
            "lien": "Parent",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/login",
        json={"email": "test@example.com", "password": "motdepasse123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/tasks",
        json={"title": "Vaisselle"},
        headers=headers,
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/tasks", headers=headers)
    assert list_response.status_code == 200
    titles = [task["title"] for task in list_response.json()]
    assert "Vaisselle" in titles


def test_list_tasks_without_token_returns_401(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401


def _creer_famille_admin_et_enfant(client):
    # L'admin s'inscrit (premier membre de la famille)
    client.post(
        "/api/signup",
        json={
            "email": "admin@example.com",
            "password": "motdepasse123",
            "name": "Admin",
            "family": "Famille Test",
            "lien": "Parent",
        },
    )
    admin_token = client.post(
        "/api/login",
        json={"email": "admin@example.com", "password": "motdepasse123"},
    ).json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # L'admin crée un compte enfant dans la même famille
    client.post(
        "/api/members",
        json={
            "email": "enfant@example.com",
            "password": "motdepasse123",
            "name": "Enfant",
            "lien": "Fils",
        },
        headers=admin_headers,
    )
    enfant_token = client.post(
        "/api/login",
        json={"email": "enfant@example.com", "password": "motdepasse123"},
    ).json()["token"]
    enfant_headers = {"Authorization": f"Bearer {enfant_token}"}

    return admin_headers, enfant_headers


def test_admin_peut_supprimer_la_tache_dun_autre_membre(client):
    admin_headers, enfant_headers = _creer_famille_admin_et_enfant(client)

    enfant_id = client.get("/api/me", headers=enfant_headers).json()["id"]
    task = client.post(
        "/api/tasks",
        json={"title": "Ranger la chambre", "member_id": enfant_id},
        headers=admin_headers,
    ).json()

    delete_response = client.delete(f"/api/tasks/{task['id']}", headers=admin_headers)
    assert delete_response.status_code == 200

    get_response = client.get(f"/api/tasks/{task['id']}", headers=admin_headers)
    assert get_response.status_code == 404


def test_non_admin_ne_peut_pas_supprimer_la_tache_dun_autre_membre(client):
    admin_headers, enfant_headers = _creer_famille_admin_et_enfant(client)

    admin_id = client.get("/api/me", headers=admin_headers).json()["id"]
    task = client.post(
        "/api/tasks",
        json={"title": "Faire les courses", "member_id": admin_id},
        headers=admin_headers,
    ).json()

    delete_response = client.delete(f"/api/tasks/{task['id']}", headers=enfant_headers)
    assert delete_response.status_code == 403
