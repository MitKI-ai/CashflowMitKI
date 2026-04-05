import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.i18n import get_translator
from app.core.logging import configure_logging, get_logger
from app.database import Base, engine
from app.graphql.schema import graphql_router
from app.web.routes.pages import router as web_router, templates

configure_logging()
logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        import structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Init FTS5 index
    from app.database import SessionLocal
    from app.services.search_service import init_fts
    with SessionLocal() as db:
        init_fts(db)
    # Register t() Jinja2 global
    templates.env.globals["get_translator"] = get_translator
    logger.info("app_started", version=settings.app_version)
    yield


app = FastAPI(
    title="Subscription Manager",
    description="Multi-Tenant SaaS Subscription Management by mitKI.ai",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key, https_only=settings.is_production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(health_router)
app.include_router(api_v1_router)
app.include_router(graphql_router, prefix="/graphql")
app.include_router(web_router)
