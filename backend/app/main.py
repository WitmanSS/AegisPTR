from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.assessments import router as assessment_router
from app.api.routes.auth import router as auth_router
from app.api.routes.findings import router as findings_router
from app.api.routes.health import router as health_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.remediation import router as remediation_router
from app.api.routes.reports import router as reports_router
from app.api.routes.retests import router as retest_router
from app.api.routes.scopes import router as scopes_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.tools import router as tools_router
from app.core.config import settings

app = FastAPI(
    title="AegisPTR",
    version="0.1.0",
    description="Pentest-to-Remediation intelligence and orchestration platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(scopes_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(findings_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(remediation_router, prefix="/api")
app.include_router(retest_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "ok",
        "environment": settings.app_env,
    }
