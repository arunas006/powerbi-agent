
from __future__ import annotations
from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.comparison import router as comparison_router
from src.api.routes.deletion import router as deletion_router
from src.api.routes.migration import router as migration_router
from src.api.routes.recommend import router as search_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Power BI Automation API",
        description="This app helps in automate the Power BI dashboard migration from Dev to Prod. It also helps in view what are the dashboard missing prod and dev workspace",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(comparison_router)
    app.include_router(deletion_router)
    app.include_router(migration_router)
    app.include_router(search_router)
    return app

app = create_app()