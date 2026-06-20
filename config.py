import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST') or os.getenv('DB_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER') or os.getenv('DB_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB') or os.getenv('DB_NAME')
