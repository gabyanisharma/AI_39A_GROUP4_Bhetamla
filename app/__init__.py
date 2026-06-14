from flask import Flask, session, redirect, url_for
from flask_mail import Mail
from config import Config
from app.translations import get_translations
from app.database import initialize_db

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Set default secret key for sessions
    app.secret_key = getattr(Config, 'SECRET_KEY', 'bhetamla_secret_key_123')

    # Initialize extensions
    mail.init_app(app)

    @app.context_processor
    def inject_translations():
        lang = session.get('language', 'en')
        return dict(t=get_translations(lang), lang=lang)

    # Initialize DB
    with app.app_context():
        initialize_db()

    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.meetup_routes import meetup_bp
    from app.routes.place_routes import place_bp
    from app.controllers.fare_alert_controller import fare_alert_bp
    from app.routes.ride_routes import ride_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(meetup_bp)
    app.register_blueprint(place_bp)
    app.register_blueprint(fare_alert_bp, url_prefix='/fare-alert')
    app.register_blueprint(ride_bp)  

    @app.route('/')
    def index():
        if session.get('user_id'):
            return redirect(url_for('user.dashboard'))
        return redirect(url_for('auth.login'))

    return app