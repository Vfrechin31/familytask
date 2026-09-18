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


def _creer_membre(client, email, password="motdepasse123", name="Membre", family="Famille", lien="Parent"):
    client.post(
        "/api/signup",
        json={"email": email, "password": password, "name": name, "family": family, "lien": lien},
    )
    token = client.post("/api/login", json={"email": email, "password": password}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_impossible_de_voir_une_tache_dune_autre_famille(client):
    headers_a = _creer_membre(client, "famillea@example.com", family="Famille A")
    headers_b = _creer_membre(client, "familleb@example.com", family="Famille B")

    task = client.post("/api/tasks", json={"title": "Tâche famille A"}, headers=headers_a).json()

    get_response = client.get(f"/api/tasks/{task['id']}", headers=headers_b)
    assert get_response.status_code == 404

    update_response = client.put(f"/api/tasks/{task['id']}", json={"done": True}, headers=headers_b)
    assert update_response.status_code == 404

    toggle_response = client.patch(f"/api/tasks/{task['id']}", headers=headers_b)
    assert toggle_response.status_code == 404


def test_join_permet_de_rejoindre_une_famille_existante(client):
    admin_headers = _creer_membre(client, "admin2@example.com", family="Famille Join")
    family_code = client.get("/api/me", headers=admin_headers).json()["family_code"]

    join_response = client.post(
        "/api/join",
        json={
            "email": "invite@example.com",
            "password": "motdepasse123",
            "name": "Invite",
            "lien": "Fille",
            "family_code": family_code,
        },
    )
    assert join_response.status_code == 201
    data = join_response.json()
    assert data["family_code"] == family_code
    assert data["is_admin"] is False

    login_response = client.post("/api/login", json={"email": "invite@example.com", "password": "motdepasse123"})
    assert login_response.status_code == 200
    invite_headers = {"Authorization": f"Bearer {login_response.json()['token']}"}

    members = client.get("/api/members", headers=admin_headers).json()
    names = [m["name"] for m in members]
    assert "Invite" in names

    # Le nouveau membre voit bien la même famille que l'admin, pas une nouvelle
    assert client.get("/api/me", headers=invite_headers).json()["family_code"] == family_code


def test_join_avec_code_inconnu_echoue(client):
    response = client.post(
        "/api/join",
        json={
            "email": "personne@example.com",
            "password": "motdepasse123",
            "name": "Personne",
            "lien": "Tonton",
            "family_code": "000000",
        },
    )
    assert response.status_code == 404
