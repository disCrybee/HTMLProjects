"""BusinessFlow REST API. Uses SQLite by default; set DATABASE_URL for PostgreSQL."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
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


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(30), default="Active")


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    value: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(30), default="Lead")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
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


app = FastAPI(title="BusinessFlow API", version="0.1.0", lifespan=lifespan)
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])


def get_db():
    with SessionLocal() as session:
        yield session


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/clients", response_model=list[ClientView])
def list_clients(db: Session = Depends(get_db)):
    return db.scalars(select(Client).order_by(Client.id.desc())).all()


@app.post("/api/clients", response_model=ClientView, status_code=201)
def create_client(payload: ClientInput, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/api/clients/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    if db.scalar(select(Deal.id).where(Deal.client_id == client_id).limit(1)):
        raise HTTPException(409, "Client has deals; delete them first")
    db.delete(client)
    db.commit()


@app.get("/api/deals", response_model=list[DealView])
def list_deals(db: Session = Depends(get_db)):
    return db.scalars(select(Deal).order_by(Deal.id.desc())).all()


@app.post("/api/deals", response_model=DealView, status_code=201)
def create_deal(payload: DealInput, db: Session = Depends(get_db)):
    if not db.get(Client, payload.client_id):
        raise HTTPException(404, "Client not found")
    deal = Deal(**payload.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.patch("/api/deals/{deal_id}", response_model=DealView)
def change_stage(deal_id: int, payload: StageUpdate, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    deal.stage = payload.stage
    db.commit()
    db.refresh(deal)
    return deal


@app.delete("/api/deals/{deal_id}", status_code=204)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    db.delete(deal)
    db.commit()


@app.get("/api/tasks", response_model=list[TaskView])
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(select(Task).order_by(Task.id.desc())).all()


@app.post("/api/tasks", response_model=TaskView, status_code=201)
def create_task(payload: TaskInput, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump(), done=False)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}", response_model=TaskView)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.done = payload.done
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()


@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db)):
    deals = db.scalars(select(Deal)).all()
    return {
        "clients": db.scalar(select(func.count(Client.id))) or 0,
        "open_tasks": db.scalar(select(func.count(Task.id)).where(Task.done.is_(False))) or 0,
        "open_pipeline": sum(d.value for d in deals if d.stage not in ("Won", "Lost")),
        "closed_won": sum(d.value for d in deals if d.stage == "Won"),
        "by_stage": {s: sum(d.stage == s for d in deals) for s in ("Lead", "Qualified", "Proposal", "Won", "Lost")},
    }
