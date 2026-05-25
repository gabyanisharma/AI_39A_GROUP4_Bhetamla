import pymysql
from config import Config

def create_database_if_not_exists():
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        connection.commit()
    finally:
        connection.close()

def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

def execute_query(query, params=None, fetch=False):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                connection.commit()
                return cursor.lastrowid
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
            phone VARCHAR(20) DEFAULT NULL,
            password_hash VARCHAR(255) NOT NULL,
            verification_token VARCHAR(255) DEFAULT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            reset_token VARCHAR(255) DEFAULT NULL,
            reset_token_expiry DATETIME DEFAULT NULL,
            profile_pic VARCHAR(255) DEFAULT NULL,
            theme_preference VARCHAR(20) DEFAULT 'light',
            language_preference VARCHAR(20) DEFAULT 'en',
            latitude DECIMAL(10,8) DEFAULT NULL,
            longitude DECIMAL(11,8) DEFAULT NULL,
            budget_preference VARCHAR(50) DEFAULT NULL,
            cuisine_preference VARCHAR(50) DEFAULT NULL,
            transport_preference VARCHAR(50) DEFAULT NULL,
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
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cancelled_at TIMESTAMP NULL DEFAULT NULL
        )""",
        """INSERT INTO users (id, full_name, email, password_hash, is_verified)
           VALUES (1, 'Bipin Maharjan', 'bipin@example.com', 'scrypt:32768:8:1$dM9wE09r7XyF$54303494e824147c45c36bcf72c3d5bbd1fb1de0e6dfb4c2b9a7b973a5a879008bc59160533dbb93ef2df7e8f5c88b9015949e29a2c317fa5cd7f1e73752fa97', TRUE)
           ON DUPLICATE KEY UPDATE id=id""",
        """INSERT INTO users (full_name, email, phone, password_hash, is_verified)
           VALUES ('John Doe', 'john.doe@example.com', '9800000000', 'scrypt:32768:8:1$yOE46sxwGDJBo9qZ$31780cf2896878940669b4d57e1e1adb3701de5a71e8e8dc59d17445008a439911b5b1f640a769fc109b585b3bc3a2cb780572017899395a7444a9b9831724a3', TRUE)
           ON DUPLICATE KEY UPDATE
               full_name = VALUES(full_name),
               phone = VALUES(phone),
               password_hash = VALUES(password_hash),
               is_verified = VALUES(is_verified)"""
    ]
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)

            cursor.execute("SHOW COLUMNS FROM sos_alerts LIKE 'cancelled_at'")
            if not cursor.fetchone():
                cursor.execute(
                    "ALTER TABLE sos_alerts "
                    "ADD COLUMN cancelled_at DATETIME DEFAULT NULL "
                    "AFTER triggered_at"
                )
        connection.commit()
    finally:
        connection.close()
