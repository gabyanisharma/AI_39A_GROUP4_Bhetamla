import os
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
    app.secret_key = getattr(Config, 'SECRET_KEY', 'bhetamla_secret_key_123')

    mail.init_app(app)

    @app.context_processor
    def inject_translations():
        lang = session.get('language', 'en')
        return dict(t=get_translations(lang), lang=lang)

    @app.context_processor
    def inject_notifications():
        if session.get('user_id'):
            from app.models.notification import Notification
            user_id = session.get('user_id')
            db_notifs = Notification.get_by_user(user_id, limit=5)
            header_notifs = []
            for n in db_notifs:
                header_notifs.append({
                    'title': n['title'],
                    'body': n['message'],
                    'time': n['created_at'].strftime('%m-%d %H:%M') if n.get('created_at') else ''
                })
            unread_count = Notification.get_unread_count(user_id)
            return dict(header_notifications=header_notifs, unread_notifications_count=unread_count)
        return dict(header_notifications=[], unread_notifications_count=0)

    with app.app_context():
        initialize_db()

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.notification_routes import notification_bp
    from app.routes.meetup_routes import meetup_bp
    from app.routes.place_routes import place_bp
    from app.controllers.fare_alert_controller import fare_alert_bp
    from app.routes.ride_routes import ride_bp
    from app.routes.explore_routes import explore_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.calendar_routes import calendar_bp
    from app.controllers.distance_controller import distance_bp

    app.register_blueprint(distance_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(meetup_bp)
    app.register_blueprint(place_bp)
    app.register_blueprint(fare_alert_bp, url_prefix='/fare-alert')
    app.register_blueprint(ride_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(calendar_bp)

    socketio.init_app(app)
    from app.socket_events import register_socket_events
    register_socket_events(socketio)

    # Start the background scheduler only in the correct process:
    # - Under the Werkzeug reloader: only in the child (WERKZEUG_RUN_MAIN=true)
    # - In production (debug=False): always start (no reloader running)
    if not app.config.get('TESTING') and (
        os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        or not app.debug
    ):
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.services.offer_reminder_service import (
            check_expiring_offers, check_meeting_reminders,
            check_fare_alerts, check_smart_alerts
        )

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=check_expiring_offers,
            args=[app],
            trigger='interval',
            hours=1,
            id='offer_reminder',
            replace_existing=True,
        )
        scheduler.add_job(
            func=check_meeting_reminders,
            args=[app],
            trigger='interval',
            minutes=30,
            id='meeting_reminders',
            replace_existing=True,
        )
        scheduler.add_job(
            func=check_fare_alerts,
            args=[app],
            trigger='interval',
            minutes=15,
            id='fare_alerts',
            replace_existing=True,
        )
        scheduler.add_job(
            func=check_smart_alerts,
            args=[app],
            trigger='interval',
            minutes=30,
            id='smart_alerts',
            replace_existing=True,
        )
        scheduler.start()

    @app.route('/')
    def index():
        return redirect(url_for('user.dashboard') if session.get('user_id') else url_for('auth.login'))

    @app.route('/users/settings', methods=['GET', 'POST'])
    def settings_plural_alias():
        from app.controllers.user_controller import settings
        return settings()

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        return render_template('errors/404.html'), 500

    return app
