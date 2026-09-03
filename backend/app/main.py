from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.models import router as models_router
from app.api.settings import router as settings_router

from app.api.databases import router as databases_router
from app.api.overview import router as overview_router
from app.api.recommendations import (
    router as recommendations_router,
)
from app.api.benchmarks import router as benchmarks_router
from app.api.workload import (
    router as workload_router,
)

app = FastAPI(
    title="DBOptima API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(databases_router)
app.include_router(overview_router)
app.include_router(recommendations_router)
app.include_router(benchmarks_router)
app.include_router(workload_router)
app.include_router(settings_router)
app.include_router(models_router)
# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }