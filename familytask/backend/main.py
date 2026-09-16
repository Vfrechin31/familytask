import os
import hashlib  # Module standard Python pour générer des empreintes (hash) de données
import secrets  # Module standard Python pour générer des chaînes aléatoires sécurisées (codes, tokens)
from typing import Optional

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import field_validator


# --- Configuration de la base de données ---

# Déclare le schéma de sécurité "Bearer token" auprès de FastAPI/Swagger
# C'est ce qui fait apparaître le bouton "Authorize" (cadenas) dans la doc
bearer_scheme = HTTPBearer() 

# URL de connexion à la base : utilise la variable d'environnement DATABASE_URL si définie,
# sinon retombe sur une base SQLite locale (pratique en dev sans dépendance externe)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")

# SQLite a besoin de cet argument pour autoriser l'accès depuis plusieurs threads
# (nécessaire car FastAPI/Uvicorn traite les requêtes de façon asynchrone)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Création du moteur de connexion à la base de données
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


# Dependency FastAPI : ouvre une session DB par requête, et la ferme proprement à la fin
def get_session():
    with Session(engine) as session:
        yield session


# --- Modèles ---

# Modèle représentant une tâche, à la fois schéma Pydantic et table SQL
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # Clé primaire, générée automatiquement par la base
    title: str  # Titre de la tâche (texte obligatoire)
    done: bool = Field(default=False)  # État de la tâche, False par défaut (non terminée)
    member_id: int = Field(foreign_key="member.id")  # À qui la tâche est assignée
    family_code: str = Field(index=True)  # Famille à laquelle appartient la tâche, indexé pour filtrer rapidement

    # Validateur exécuté automatiquement à chaque création/validation d'un Task
    @field_validator("title")
    @classmethod
    def title_non_vide(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Le titre de la tâche ne peut pas être vide")
        return value


# Modèle utilisé pour la mise à jour partielle d'une tâche (tous les champs optionnels)
class TaskUpdate(SQLModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# Modèle représentant les données envoyées pour créer une tâche
# (member_id est optionnel : absent = la tâche est pour soi-même)
class TaskCreate(SQLModel):
    title: str
    done: bool = False
    member_id: Optional[int] = None

# Modèle représentant un membre de la famille, à la fois schéma Pydantic et table SQL
class Member(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # Clé primaire, générée automatiquement par la base
    email: str = Field(unique=True, index=True)  # Email unique (contrainte en base) et indexé (recherche rapide)
    name: str  # Nom affiché du membre
    lien: str  # Lien de parenté ou relation dans la famille (ex. "Maman", "Fils")
    is_admin: bool = Field(default=False)  # Rôle admin ou non, faux par défaut
    family_code: str = Field(index=True)  # Code de la famille, indexé pour retrouver rapidement tous les membres d'une même famille
    password_hash: str  # Empreinte du mot de passe (jamais le mot de passe en clair)
    token: Optional[str] = None  # Jeton de session/authentification, optionnel (absent tant que le membre n'est pas connecté)


# Modèle représentant les données envoyées lors de l'inscription
class SignupRequest(SQLModel):
    email: str
    password: str
    name: str
    family: str  # Nom de la famille (utilisé pour générer le family_code, pas stocké tel quel)
    lien: str


# Modèle représentant les données envoyées lors de la connexion
class LoginRequest(SQLModel):
    email: str
    password: str


# Modèle de réponse pour /api/me : exclut délibérément password_hash et token
class MemberPublic(SQLModel):
    id: int
    email: str
    name: str
    lien: str
    is_admin: bool
    family_code: str


# Modèle représentant les données envoyées pour créer un compte membre (par un admin)
class MemberCreate(SQLModel):
    email: str
    password: str
    name: str
    lien: str
    is_admin: bool = False


# Modèle représentant un lien de parenté, propre à une famille (ex. "Maman", "Fils", "Tonton")
# C'est la liste modifiable dans laquelle les membres piochent pour leur champ "lien"
class Lien(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # Clé primaire, générée automatiquement par la base
    nom: str  # Libellé du lien de parenté (ex. "Maman")
    family_code: str = Field(index=True)  # Famille à laquelle appartient ce lien, indexé pour filtrer rapidement

    # Validateur exécuté automatiquement à chaque création/validation d'un Lien
    @field_validator("nom")
    @classmethod
    def nom_non_vide(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Le nom du lien ne peut pas être vide")
        return value


# Modèle représentant les données envoyées pour créer un lien de parenté
class LienCreate(SQLModel):
    nom: str


# --- Fonctions utilitaires ---

# Fonction utilitaire qui transforme un mot de passe en clair en une empreinte SHA-256
def hash_password(pw: str) -> str:
    # .encode() convertit la chaîne de caractères en octets, requis par hashlib
    # .hexdigest() renvoie l'empreinte sous forme de chaîne hexadécimale lisible
    return hashlib.sha256(pw.encode()).hexdigest()


# Dépendance FastAPI : identifie le membre connecté à partir du token Bearer fourni via Swagger/Authorize
def get_current_member(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session)
) -> Member:
    # FastAPI a déjà vérifié que l'en-tête est bien au format "Bearer <token>" et extrait le token
    # credentials.credentials contient uniquement le token, sans le préfixe "Bearer "
    token = credentials.credentials

    # On récupère le membre dont le token en base correspond exactement à celui envoyé
    member = session.exec(select(Member).where(Member.token == token)).first()

    # Si aucun membre ne correspond (token invalide, absent, ou déjà déconnecté), on refuse l'accès
    if not member:
        raise HTTPException(status_code=401, detail="Authentification requise")

    return member

# Fonction qui crée toutes les tables définies par les modèles SQLModel si elles n'existent pas déjà
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# --- Application ---

app = FastAPI(title="FamilyTask")  # Instance principale de l'application FastAPI
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # Autorise toutes les origines, méthodes et en-têtes


# Événement exécuté automatiquement au démarrage de l'application
@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # On crée les tables dès que le serveur démarre


@app.get("/api/health")
def health():
    return {"status": "ok"}

# --- Routes Task ---

# GET /api/tasks : renvoie uniquement les tâches assignées au membre connecté
@app.get("/api/tasks", response_model=list[Task])
def list_tasks(current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    tasks = session.exec(select(Task).where(Task.member_id == current_member.id)).all()
    return tasks


# GET /api/tasks/famille : renvoie toutes les tâches de la famille (admin uniquement)
# Placée AVANT /api/tasks/{task_id} pour éviter tout conflit de route
@app.get("/api/tasks/famille", response_model=list[Task])
def list_family_tasks(current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    if not current_member.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    tasks = session.exec(select(Task).where(Task.family_code == current_member.family_code)).all()
    return tasks


# GET /api/tasks/{task_id} : renvoie une tâche précise par son id, ou 404 si elle n'existe pas
@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return task


# POST /api/tasks : crée une tâche pour soi-même, ou pour un autre membre de sa famille si on est admin
@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(
    data: TaskCreate,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session)
):
    # Par défaut, la tâche est assignée à soi-même
    assigned_member_id = current_member.id

    # Si un member_id différent est fourni, on vérifie les droits avant d'assigner à quelqu'un d'autre
    if data.member_id is not None and data.member_id != current_member.id:
        if not current_member.is_admin:
            raise HTTPException(status_code=403, detail="Seul un administrateur peut assigner une tâche à un autre membre")

        # On vérifie que le membre ciblé existe bien et appartient à la même famille
        target_member = session.get(Member, data.member_id)
        if not target_member or target_member.family_code != current_member.family_code:
            raise HTTPException(status_code=404, detail="Membre introuvable dans votre famille")

        assigned_member_id = data.member_id

    task = Task(
        title=data.title,
        done=data.done,
        member_id=assigned_member_id,
        family_code=current_member.family_code  # La famille vient toujours du compte connecté, jamais du client
    )

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# PUT /api/tasks/{task_id} : met à jour une tâche existante (partiellement) ou renvoie 404
@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    # On ne met à jour que les champs réellement envoyés par le client
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# DELETE /api/tasks/{id} : supprime une tâche existante et renvoie un message de confirmation
@app.delete("/api/tasks/{id}")
def delete_task(id: int, session: Session = Depends(get_session)):
    # Recherche de la tâche par sa clé primaire
    task = session.get(Task, id)

    # Si aucune tâche ne correspond à cet id, on renvoie une erreur 404
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    session.delete(task)  # On marque la tâche pour suppression
    session.commit()      # On valide la transaction (suppression réelle en base)

    # On renvoie un message de confirmation en JSON plutôt qu'une réponse vide
    return {"message": f"Tâche {id} supprimée avec succès"}


# PATCH /api/tasks/{id} : inverse l'état "done" d'une tâche existante (true -> false, false -> true)
@app.patch("/api/tasks/{id}", response_model=Task)
def toggle_task(id: int, session: Session = Depends(get_session)):
    # Recherche de la tâche par sa clé primaire
    task = session.get(Task, id)

    # Si aucune tâche ne correspond à cet id, on renvoie une erreur 404
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    # On inverse simplement la valeur booléenne actuelle
    task.done = not task.done

    session.add(task)      # On prépare la mise à jour
    session.commit()       # On valide la transaction (écrit réellement en base)
    session.refresh(task)  # On recharge l'objet pour être sûr d'avoir la valeur à jour

    return task  # FastAPI sérialise automatiquement la tâche modifiée en JSON


# --- Routes Member (authentification) ---

# POST /api/signup : crée le tout premier membre d'une nouvelle famille (admin par défaut)
@app.post("/api/signup", response_model=MemberPublic, status_code=201)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    # On vérifie qu'aucun membre n'existe déjà avec cet email, pour éviter les doublons de compte
    existing = session.exec(select(Member).where(Member.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=422, detail="Un compte existe déjà avec cet email")

    # Génération d'un code de famille aléatoire et lisible (ex. "3F9A2C")
    family_code = secrets.token_hex(3).upper()

    # Génération d'un token d'authentification aléatoire et sécurisé
    token = secrets.token_hex(32)

    # Création du membre : premier de la famille, donc administrateur par défaut
    member = Member(
        email=data.email,
        name=data.name,
        lien=data.lien,
        is_admin=True,
        family_code=family_code,
        password_hash=hash_password(data.password),  # On ne stocke jamais le mot de passe en clair
        token=token
    )

    session.add(member)
    session.commit()
    session.refresh(member)

    return member  # response_model=MemberPublic filtre automatiquement password_hash et token

# GET /api/members : renvoie tous les membres de la même famille que le membre connecté,
# moi compris (le membre connecté n'est volontairement pas exclu de la liste)
@app.get("/api/members", response_model=list[MemberPublic])
def list_members(current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    members = session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()
    return members


# POST /api/members : crée un compte membre dans ma famille (admin uniquement)
@app.post("/api/members", response_model=MemberPublic, status_code=201)
def create_member(
    data: MemberCreate,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session)
):
    # Seul un administrateur peut créer un compte pour un membre de sa famille
    if not current_member.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    # On vérifie qu'aucun membre n'existe déjà avec cet email, pour éviter les doublons de compte
    existing = session.exec(select(Member).where(Member.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=422, detail="Un compte existe déjà avec cet email")

    member = Member(
        email=data.email,
        name=data.name,
        lien=data.lien,
        is_admin=data.is_admin,
        family_code=current_member.family_code,  # Le nouveau membre rejoint toujours la famille de l'admin qui le crée
        password_hash=hash_password(data.password),  # On ne stocke jamais le mot de passe en clair
        token=None  # Pas de token tant que le membre ne s'est pas connecté lui-même
    )

    session.add(member)
    session.commit()
    session.refresh(member)

    return member  # response_model=MemberPublic filtre automatiquement password_hash et token


# DELETE /api/members/{id} : supprime un compte membre et ses tâches (admin uniquement)
@app.delete("/api/members/{id}")
def delete_member(id: int, current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    # Seul un administrateur peut supprimer un compte membre
    if not current_member.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    # Interdit de se supprimer soi-même, pour ne jamais se retrouver sans accès à sa propre famille
    if id == current_member.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")

    # Le membre ciblé doit exister et appartenir à la même famille que l'administrateur
    member = session.get(Member, id)
    if not member or member.family_code != current_member.family_code:
        raise HTTPException(status_code=404, detail="Membre introuvable dans votre famille")

    # Un administrateur ne peut pas supprimer un autre administrateur (seulement soi-même via la règle ci-dessus,
    # déjà interdit) : évite qu'un admin ne supprime accidentellement ou intentionnellement un autre parent admin
    if member.is_admin:
        raise HTTPException(status_code=403, detail="Impossible de supprimer un autre administrateur")

    # On supprime d'abord toutes les tâches assignées à ce membre, pour ne pas laisser de tâches orphelines
    tasks = session.exec(select(Task).where(Task.member_id == id)).all()
    for task in tasks:
        session.delete(task)

    session.delete(member)  # On marque le membre pour suppression
    session.commit()        # On valide la transaction (suppression réelle en base)

    return {"message": f"Membre {id} supprimé avec succès"}


# POST /api/login : authentifie un membre existant et lui génère un nouveau token
@app.post("/api/login")
def login(data: LoginRequest, session: Session = Depends(get_session)):
    # Recherche du membre par email
    member = session.exec(select(Member).where(Member.email == data.email)).first()

    # Message volontairement neutre : on ne précise pas si c'est l'email ou le mot de passe qui est faux,
    # pour ne pas donner d'indice à quelqu'un qui tenterait de deviner des comptes existants
    if not member or member.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Génération d'un nouveau token à chaque connexion (invalide l'ancien)
    member.token = secrets.token_hex(32)
    session.add(member)
    session.commit()
    session.refresh(member)

    return {"token": member.token}


# GET /api/me : renvoie les informations du membre actuellement connecté (sans données sensibles)
@app.get("/api/me", response_model=MemberPublic)
def get_me(current_member: Member = Depends(get_current_member)):
    return current_member


# POST /api/logout : déconnecte le membre en supprimant son token en base
@app.post("/api/logout")
def logout(current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    current_member.token = None  # Le token n'est plus valide, toute requête future avec l'ancien token échouera
    session.add(current_member)
    session.commit()
    return {"message": "Déconnexion réussie"}


# --- Routes Lien (liens de parenté) ---

# GET /api/liens : renvoie la liste des liens de parenté propres à ma famille
@app.get("/api/liens", response_model=list[Lien])
def list_liens(current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    liens = session.exec(select(Lien).where(Lien.family_code == current_member.family_code)).all()
    return liens


# POST /api/liens : ajoute un nouveau lien de parenté à ma famille
@app.post("/api/liens", response_model=Lien, status_code=201)
def create_lien(
    data: LienCreate,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session)
):
    lien = Lien(
        nom=data.nom,
        family_code=current_member.family_code  # La famille vient toujours du compte connecté, jamais du client
    )

    session.add(lien)
    session.commit()
    session.refresh(lien)
    return lien


# DELETE /api/liens/{id} : supprime un lien de parenté de ma famille (admin uniquement)
@app.delete("/api/liens/{id}")
def delete_lien(id: int, current_member: Member = Depends(get_current_member), session: Session = Depends(get_session)):
    if not current_member.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    lien = session.get(Lien, id)
    if not lien or lien.family_code != current_member.family_code:
        raise HTTPException(status_code=404, detail="Lien de parenté introuvable dans votre famille")

    session.delete(lien)
    session.commit()

    return {"message": f"Lien {id} supprimé avec succès"}