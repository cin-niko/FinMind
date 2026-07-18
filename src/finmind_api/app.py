from fastapi import FastAPI

from finmind_agents.runtime.offload import configure_sync_offload_limit
from finmind_api.auth import SessionService
from finmind_api.platform import create_demo_platform
from finmind_api.preferences_store import LanguagePreferenceStore
from finmind_api.routes import register_routes
from finmind_api.settings import Settings
from finmind_api.streaming import StreamConcurrencyLimiter


def create_app() -> FastAPI:
    settings = Settings.from_env()
    app = FastAPI(title="FinMind API")
    app.state.settings = settings
    app.state.session_service = SessionService(settings)
    app.state.language_preferences = LanguagePreferenceStore()
    app.state.platform = create_demo_platform()
    app.state.stream_limiter = StreamConcurrencyLimiter(
        global_limit=settings.stream_global_limit,
        per_user_limit=settings.stream_per_user_limit,
    )
    app.state.stream_heartbeat_seconds = settings.stream_heartbeat_seconds
    configure_sync_offload_limit(settings.sync_offload_limit)
    register_routes(app)
    return app
