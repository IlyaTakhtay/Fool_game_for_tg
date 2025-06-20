from backend.api.middlewares.cors_middleware import add_cors_middleware
from backend.api.middlewares.errors_middleware import error_handling_middleware

def setup_middlewares(app):
    add_cors_middleware(app)
    # error_handling_middleware(app)
