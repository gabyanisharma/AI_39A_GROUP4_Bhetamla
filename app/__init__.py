<<<<<<< HEAD
from flask import Flask
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mail.init_app(app)

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.meetup_routes import meetup_bp
    from app.routes.place_routes import place_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(meetup_bp)
    app.register_blueprint(place_bp)

    return app
=======
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
>>>>>>> 97de5e1540905497f4b5c931e91c6ee8dc690f79
