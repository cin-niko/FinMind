from fastapi import FastAPI

from api.auth import SessionService
from api.platform.factory import create_demo_platform
from api.routes import register_routes
from api.settings import Settings


def create_app() -> FastAPI:
    settings = Settings.from_env()
    app = FastAPI(title="FinMind API")
    app.state.settings = settings
    app.state.session_service = SessionService(settings)
    app.state.platform = create_demo_platform(settings)
    register_routes(app)
    return app
