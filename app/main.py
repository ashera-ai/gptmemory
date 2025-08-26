# app/main.py (final known-good)

from datetime import datetime
import os
from typing import Any, List, Optional

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column
from sqlalchemy.types import JSON as SAJSON

# ----- Database setup -----
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})

# ----- Models -----
class Entry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    data: dict = Field(sa_column=Column(SAJSON))

class PostPayload(BaseModel):
    data: Optional[Any] = None

# ----- App -----
app = FastAPI(title="FastAPI on Render — Minimal Data Store")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/", include_in_schema=False)
def health():
    return {"status": "ok", "endpoints": ["/data (GET, POST)", "/docs"]}

@app.post("/data", response_model=Entry)
async def create_data(payload: Optional[PostPayload] = None, request: Request = None):
    if payload and payload.data is not None:
        to_store = payload.data
    else:
        try:
            to_store = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

    with Session(engine) as session:
        entry = Entry(data=to_store)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

@app.get("/data", response_model=List[Entry])
def list_data():
    with Session(engine) as session:
        stmt = select(Entry).order_by(Entry.created_at.asc())
        return list(session.exec(stmt))

# ---- Keep this at the very bottom ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
