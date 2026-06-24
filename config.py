import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Database ──────────────────────────────────────────────────────────────
    MYSQL_HOST     = os.getenv('MYSQL_HOST') or os.getenv('DB_HOST')
    MYSQL_USER     = os.getenv('MYSQL_USER') or os.getenv('DB_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD')
    MYSQL_DB       = os.getenv('MYSQL_DB') or os.getenv('DB_NAME')

    # ── App ───────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv('SECRET_KEY', 'bhetamla_secret_key_123')

    # ── Flask-Mail ────────────────────────────────────────────────────────────
    # Leave these blank in .env to skip email sending gracefully.
    MAIL_SERVER          = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT            = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS         = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME        = os.getenv('MAIL_USERNAME')        # None if not set → mail skipped
    MAIL_PASSWORD        = os.getenv('MAIL_PASSWORD')        # None if not set → mail skipped
    MAIL_DEFAULT_SENDER  = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
