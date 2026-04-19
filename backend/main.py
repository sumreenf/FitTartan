"""FitTartan FastAPI entry — SQLite, CMU dining cache, LangGraph agent."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import agent_router, content, crowd_router, eval_router, logs, users
from scraper import sync_menu_to_db
from database import SessionLocal

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        sync_menu_to_db(db)
    except Exception:
        pass
    finally:
        db.close()
    yield


app = FastAPI(title="FitTartan API", lifespan=lifespan)

_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(logs.router)
app.include_router(agent_router.router)
app.include_router(crowd_router.router)
app.include_router(content.router)
app.include_router(eval_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
