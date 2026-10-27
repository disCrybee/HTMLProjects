"""BusinessFlow REST API. Uses SQLite by default; set DATABASE_URL for PostgreSQL."""
import os
from contextlib import asynccontextmanager
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import secrets
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./businessflow.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(30), default="Active")


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    value: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(30), default="Lead")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    due: Mapped[str] = mapped_column(String(80), default="")
    done: Mapped[bool] = mapped_column(Boolean, default=False)


Stage = Literal["Lead", "Qualified", "Proposal", "Won", "Lost"]


class ClientInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    company: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    status: Literal["Active", "Lead"] = "Active"


class ClientView(ClientInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DealInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    client_id: int
    value: int = Field(gt=0, le=1_000_000_000)
    stage: Stage = "Lead"


class DealView(DealInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StageUpdate(BaseModel):
    stage: Stage


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due: str = Field(default="", max_length=80)


class TaskView(TaskInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    done: bool


class TaskUpdate(BaseModel):
    done: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="BusinessFlow API", version="0.3.0", lifespan=lifespan)
bearer = HTTPBearer(auto_error=False)


def get_db():
    with SessionLocal() as session:
        yield session


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(stored)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode(), raw[:16], 310000)
        return hmac.compare_digest(raw[16:], expected)
    except (ValueError, TypeError):
        return False


def sign_token(user_id: int) -> str:
    secret = os.getenv("BUSINESSFLOW_SESSION_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(503, "Session secret not configured")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "exp": int(time.time()) + 3600}).encode()).rstrip(b"=").decode()
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def current_user(credentials: HTTPAuthorizationCredentials | None = Security(bearer), db: Session = Depends(get_db)) -> User:
    secret = os.getenv("BUSINESSFLOW_SESSION_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(503, "Session secret not configured")
    error = HTTPException(401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    if not credentials:
        raise error
    try:
        body, signature = credentials.credentials.split(".")
        valid = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, valid):
            raise error
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if not isinstance(data.get("sub"), int) or data.get("exp", 0) <= time.time():
            raise error
    except (ValueError, KeyError, TypeError):
        raise error
    user = db.get(User, data["sub"])
    if not user:
        raise error
    return user


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)


@app.post("/auth/register", status_code=201)
def register(payload: Credentials, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Invalid email")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Account already exists")
    from sqlalchemy.exc import IntegrityError
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account already exists")
    db.refresh(user)
    return {"access_token": sign_token(user.id), "token_type": "bearer"}


@app.post("/auth/login")
def login(payload: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": sign_token(user.id), "token_type": "bearer"}


@app.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email}


origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type", "Authorization"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/clients", response_model=list[ClientView], dependencies=[Depends(current_user)])
def list_clients(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Client).where(Client.owner_id == user.id).order_by(Client.id.desc())).all()


@app.post("/api/clients", response_model=ClientView, status_code=201, dependencies=[Depends(current_user)])
def create_client(payload: ClientInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    client = Client(**payload.model_dump(), owner_id=user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/api/clients/{client_id}", status_code=204, dependencies=[Depends(current_user)])
def delete_client(client_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    if db.scalar(select(Deal.id).where(Deal.client_id == client_id, Deal.owner_id == user.id).limit(1)):
        raise HTTPException(409, "Client has deals; delete them first")
    db.delete(client)
    db.commit()


@app.get("/api/deals", response_model=list[DealView], dependencies=[Depends(current_user)])
def list_deals(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Deal).where(Deal.owner_id == user.id).order_by(Deal.id.desc())).all()


@app.post("/api/deals", response_model=DealView, status_code=201, dependencies=[Depends(current_user)])
def create_deal(payload: DealInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.scalar(select(Client).where(Client.id == payload.client_id, Client.owner_id == user.id)):
        raise HTTPException(404, "Client not found")
    deal = Deal(**payload.model_dump(), owner_id=user.id)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.patch("/api/deals/{deal_id}", response_model=DealView, dependencies=[Depends(current_user)])
def change_stage(deal_id: int, payload: StageUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    deal.stage = payload.stage
    db.commit()
    db.refresh(deal)
    return deal


@app.delete("/api/deals/{deal_id}", status_code=204, dependencies=[Depends(current_user)])
def delete_deal(deal_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    db.delete(deal)
    db.commit()


@app.get("/api/tasks", response_model=list[TaskView], dependencies=[Depends(current_user)])
def list_tasks(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Task).where(Task.owner_id == user.id).order_by(Task.id.desc())).all()


@app.post("/api/tasks", response_model=TaskView, status_code=201, dependencies=[Depends(current_user)])
def create_task(payload: TaskInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    task = Task(**payload.model_dump(), done=False, owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}", response_model=TaskView, dependencies=[Depends(current_user)])
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.done = payload.done
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204, dependencies=[Depends(current_user)])
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()


@app.get("/api/metrics", dependencies=[Depends(current_user)])
def metrics(db: Session = Depends(get_db), user: User = Depends(current_user)):
    deals = db.scalars(select(Deal).where(Deal.owner_id == user.id)).all()
    return {
        "clients": db.scalar(select(func.count(Client.id)).where(Client.owner_id == user.id)) or 0,
        "open_tasks": db.scalar(select(func.count(Task.id)).where(Task.done.is_(False), Task.owner_id == user.id)) or 0,
        "open_pipeline": sum(d.value for d in deals if d.stage not in ("Won", "Lost")),
        "closed_won": sum(d.value for d in deals if d.stage == "Won"),
        "by_stage": {s: sum(d.stage == s for d in deals) for s in ("Lead", "Qualified", "Proposal", "Won", "Lost")},
    }
