from datetime import datetime
import os
from typing import Any, List, Optional

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column
from sqlalchemy.types import JSON as SAJSON

# ----- Database setup (SQLite by default; supports Postgres via DATABASE_URL) -----
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g., "postgresql+psycopg://user:pass@host/db"
if DATABASE_URL:
    # Render Postgres uses SSL; SQLAlchemy + psycopg handles this automatically.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Local/persistent file; on Render this persists only if you attach a Disk.
    engine = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})

# ----- Models -----
class Entry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    # Store arbitrary JSON payloads
    data: dict = Field(sa_column=Column(SAJSON))

class PostPayload(BaseModel):
    # Accept any JSON; if the client posts raw JSON (not wrapped), we'll store it directly.
    # If the client sends {"data": {...}}, we accept that too.
    data: Optional[Any] = None

# ----- App -----
app = FastAPI(title="FastAPI on Render — Minimal Data Store")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/data", response_model=Entry)
async def create_data(payload: Optional[PostPayload] = None, request: Request = None):
    # Allow two styles:
    # 1) Raw JSON: POST {...}            -> store that
    # 2) Wrapped : POST {"data": {...}}  -> store payload.data
    if payload and payload.data is not None:
        to_store = payload.data
    else:
        # If user posted raw JSON, FastAPI put it in the request body
        try:
            to_store = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

    entry = Entry(data=to_store)
    with Session(engine) as session:
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

@app.get("/data", response_model=List[Entry])
def list_data():
    with Session(engine) as session:
        stmt = select(Entry).order_by(Entry.created_at.asc())
        return list(session.exec(stmt))
