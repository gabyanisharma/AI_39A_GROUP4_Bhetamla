import os
from datetime import datetime, timedelta

from flask import Flask

from app.routes.auth import AuthRoutes


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "bhetam-dev-secret-key"),
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        TEMPLATES_AUTO_RELOAD=True,
    )

    if test_config:
        app.config.update(test_config)

    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register_routes())

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.now().year}

    return app
