import pymysql
from app.config import Config

def create_database_if_not_exists():
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        connection.commit()
    finally:
        connection.close()

def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )

def execute_query(query, params=None, fetch=False):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None
            connection.commit()
            return result
    finally:
        connection.close()

def initialize_db():
    """Run this once to create your database and tables if they don't exist."""
    create_database_if_not_exists()
    
    queries = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            relationship VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS sos_alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            message TEXT,
            status ENUM('active', 'cancelled', 'resolved') DEFAULT 'active',
            cancel_pin VARCHAR(10),
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """INSERT INTO users (id, full_name, email, password)
           VALUES (1, 'Bipin Maharjan', 'bipin@example.com', 'password123')
           ON DUPLICATE KEY UPDATE id=id"""
    ]
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)
        connection.commit()
    finally:
        connection.close()