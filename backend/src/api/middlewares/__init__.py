from backend.src.api.middlewares.cors_middleware import add_cors_middleware
from backend.src.api.middlewares.errors_middleware import error_handling_middleware
from backend.src.api.middlewares.logging_middleware import logging_middleware
from backend.src.settings import CorsSettings


def setup_middlewares(app, cors_settings: CorsSettings):
    app.middleware("http")(logging_middleware)
    add_cors_middleware(app, cors_settings)
    # error_handling_middleware(app)
