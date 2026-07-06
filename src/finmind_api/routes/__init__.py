from fastapi import FastAPI

from finmind_api.routes import artifacts, auth, runs, workflows


def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(workflows.router)
    app.include_router(runs.router)
    app.include_router(artifacts.router)
