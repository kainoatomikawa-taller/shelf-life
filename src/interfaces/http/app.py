"""FastAPI application factory and entry point.

Wires the HTTP delivery mechanism together. Run with:

    uvicorn src.interfaces.http.app:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.interfaces.http.controllers.catalog_controller import (
    router as catalog_router,
)
from src.interfaces.http.controllers.cook_now_controller import (
    router as cook_now_router,
)
from src.interfaces.http.controllers.discover_controller import (
    router as discover_router,
)
from src.interfaces.http.controllers.inventory_controller import (
    router as inventory_router,
)
from src.interfaces.http.controllers.pantry_controller import (
    router as pantry_router,
)
from src.interfaces.http.controllers.shopping_list_controller import (
    router as shopping_list_router,
)
from src.interfaces.http.controllers.user_controller import (
    router as user_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup: create tables in development. Use Alembic migrations in prod.
    from src.infrastructure.config import settings
    from src.infrastructure.database.engine import init_db

    if settings.app_env == "development":
        await init_db()
    yield
    # Shutdown hooks (close pools, etc.) would go here.


def create_app() -> FastAPI:
    app = FastAPI(
        title="Shelf Life API",
        description="Track your pantry and never let food expire again.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(pantry_router)
    app.include_router(user_router)
    app.include_router(catalog_router)
    app.include_router(inventory_router)
    app.include_router(cook_now_router)
    app.include_router(discover_router)
    app.include_router(shopping_list_router)
    return app


app = create_app()
