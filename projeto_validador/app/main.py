"""
FastAPI application factory with lifespan management.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.api.auth import router as auth_router
from app.database.session import close_db, init_db, async_session_factory
from app.database.models import User
from app.api.auth_utils import get_password_hash
from sqlalchemy import select


async def seed_admin_user():
    """Seed the default admin@admin user if it doesn't exist."""
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == "admin@admin"))
        user = result.scalar_one_or_none()
        if not user:
            admin = User(
                email="admin@admin",
                hashed_password=get_password_hash("admin"),
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print("Admin user seeded: admin@admin / admin")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: init DB on startup, close on shutdown."""
    await init_db()
    await seed_admin_user()
    yield
    await close_db()


app = FastAPI(
    title="Pre-Flight Validation System",
    description="Sistema Multi-Agentes de Validação Pré-Flight Gráfico",
    version="1.0.0",
    lifespan=lifespan,
)

# Middlewares

logger = logging.getLogger(__name__)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    request.state.request_id = request_id
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"req_id={request_id} method={request.method} path={request.url.path} status={response.status_code} duration={process_time:.4f}s"
    )
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers (RFC 9457 Problem Details)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
        content={
            "type": "about:blank",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path
        },
        media_type="application/problem+json"
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Validation Error",
            "status": 422,
            "detail": exc.errors(),
            "instance": request.url.path
        },
        media_type="application/problem+json"
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
            "instance": request.url.path
        },
        media_type="application/problem+json"
    )

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(jobs_router)
