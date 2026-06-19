from fastapi import FastAPI

from api.routes import auth, runs, workflows


def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(workflows.router)
    app.include_router(runs.router)
