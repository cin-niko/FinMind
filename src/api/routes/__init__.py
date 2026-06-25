from fastapi import FastAPI

from api.routes import admin, auth, market, runs, workflows


def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(market.router)
    app.include_router(workflows.router)
    app.include_router(runs.router)
