import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'bhetamla-secret-2024')

    MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER     = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
    MYSQL_DB       = os.getenv('MYSQL_DB', 'bhetamla_db')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', MYSQL_DB)

    MAIL_SERVER  = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT    = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME       = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD       = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')