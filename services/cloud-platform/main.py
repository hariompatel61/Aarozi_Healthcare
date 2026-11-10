"""Aarozi Healthcare — Hosted Cloud Platform API.

Entrypoint for the hosted multi-tenant management platform.
Connects to PostgreSQL (Supabase / Neon / Railway / AWS RDS).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base
from routes.admin_routes import router as admin_router

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    dev_db = Path(__file__).resolve().parent / "database" / "cloud_dev.db"
    DATABASE_URL = f"sqlite:///{dev_db}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(
    title="Aarozi Healthcare — Cloud Platform SaaS API",
    version="2.4.0",
    description="Backend service for Hosted Super Admin Console, Razorpay billing, and public website CMS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cloud-platform", "version": "2.4.0"}
