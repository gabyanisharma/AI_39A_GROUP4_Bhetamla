from flask import Flask, session
from flask_mail import Mail
from config import Config
from app.translations import get_translations

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)

    @app.context_processor
    def inject_translations():
        lang = session.get('language', 'en')
        return dict(t=get_translations(lang), lang=lang)

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.meetup_routes import meetup_bp
    from app.routes.place_routes import place_bp
    from app.routes.notification_routes import notification_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(meetup_bp)
    app.register_blueprint(place_bp)
    app.register_blueprint(notification_bp)

    return app