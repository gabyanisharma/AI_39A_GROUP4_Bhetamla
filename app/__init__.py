from flask import Flask, session, redirect, url_for
from flask_mail import Mail
from flask_socketio import SocketIO
from config import Config
from app.translations import get_translations
from app.database import initialize_db

mail = Mail()
socketio = SocketIO(cors_allowed_origins='*', async_mode='threading')

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

    @app.context_processor
    def inject_notifications():
        if session.get('user_id'):
            from app.models.place import RestaurantOffer
            user_id = session.get('user_id')
            offers = RestaurantOffer.get_saved_by_user(user_id)
            expiring_offers = []
            if offers:
                for o in offers:
                    if o['remind_me']:
                        expiring_offers.append({
                            'title': 'Offer Expiring Soon!',
                            'body': f"{o['title']} at {o['restaurant_name']} expires on {o['valid_until']}.",
                            'time': 'Just now'
                        })
            return dict(header_notifications=expiring_offers)
        return dict(header_notifications=[])

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
    from app.routes.explore_routes import explore_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(meetup_bp)
    app.register_blueprint(place_bp)
    app.register_blueprint(fare_alert_bp, url_prefix='/fare-alert')
    app.register_blueprint(ride_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(analytics_bp)

    socketio.init_app(app)
    from app.socket_events import register_socket_events
    register_socket_events(socketio)

    # Proactive notification scheduler (meeting reminders, smart alerts, fare
    # drops). Disable with BHETAMLA_SCHEDULER=0 (e.g. during tests).
    import os as _os
    if _os.environ.get('BHETAMLA_SCHEDULER', '1') != '0':
        try:
            from app.services.background_scheduler import start as _start_scheduler
            _start_scheduler(app)
        except Exception as _e:
            print(f'Scheduler not started: {_e}')

    @app.route('/')
    def index():
        if session.get('user_id'):
            return redirect(url_for('user.dashboard'))
        return redirect(url_for('auth.login'))

    return app

def get_socketio():
    return socketio