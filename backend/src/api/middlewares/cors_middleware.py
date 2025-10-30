from fastapi.middleware.cors import CORSMiddleware
from backend.src.config import CorsSettings


def add_cors_middleware(app, cors_settings: CorsSettings):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
