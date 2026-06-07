import pymysql
from config import Config
from datetime import time, timedelta
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions


def _convert_time(value):
    """Return MySQL TIME values as datetime.time for template formatting."""
    if value is None or isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds()) % 86400
        return time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)
    if isinstance(value, bytes):
        value = value.decode()
    if isinstance(value, str):
        value = value.split('.')[0]
        negative = value.startswith('-')
        if negative:
            value = value[1:]
        parts = [int(part) for part in value.split(':')]
        while len(parts) < 3:
            parts.append(0)
        hours, minutes, seconds = parts[:3]
        return time(hours % 24, minutes, seconds)
    return value


DB_CONVERSIONS = conversions.copy()
DB_CONVERSIONS[FIELD_TYPE.TIME] = _convert_time

def create_database_if_not_exists():
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor,
        conv=DB_CONVERSIONS
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
        cursorclass=pymysql.cursors.DictCursor,
        conv=DB_CONVERSIONS
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
    import os
    create_database_if_not_exists()
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Split on semicolon for multi-statement execution
    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            _repair_existing_schema(cursor)
            _seed_demo_data(cursor)
        connection.commit()
    finally:
        connection.close()


def _column_exists(cursor, table, column):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
    return cursor.fetchone() is not None


def _ensure_column(cursor, table, column, definition):
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {definition}")


def _repair_existing_schema(cursor):
    """Add columns that older local databases may be missing."""
    _ensure_column(cursor, 'users', 'role', "role ENUM('user', 'admin') DEFAULT 'user'")
    _ensure_column(cursor, 'users', 'updated_at',
                   "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    _ensure_column(cursor, 'sos_alerts', 'cancelled_at', "cancelled_at TIMESTAMP NULL")
    _ensure_column(cursor, 'meetups', 'group_id', "group_id INT NULL")
    _ensure_column(cursor, 'meetups', 'midpoint_lat', "midpoint_lat DECIMAL(10,8) NULL")
    _ensure_column(cursor, 'meetups', 'midpoint_lng', "midpoint_lng DECIMAL(11,8) NULL")
    _ensure_column(cursor, 'meetups', 'midpoint_address', "midpoint_address VARCHAR(255) NULL")
    _ensure_column(cursor, 'meetups', 'meetup_date', "meetup_date DATE NULL")
    _ensure_column(cursor, 'meetups', 'meetup_time', "meetup_time TIME NULL")
    _ensure_column(cursor, 'restaurants', 'image_url', "image_url VARCHAR(255) NULL")


def _seed_demo_data(cursor):
    users = [
        (
            'Bipin Maharjan',
            'bipin@example.com',
            '9800000001',
            'scrypt:32768:8:1$dM9wE09r7XyF$54303494e824147c45c36bcf72c3d5bbd1fb1de0e6dfb4c2b9a7b973a5a879008bc59160533dbb93ef2df7e8f5c88b9015949e29a2c317fa5cd7f1e73752fa97',
        ),
        (
            'John Doe',
            'john.doe@example.com',
            '9800000000',
            'scrypt:32768:8:1$yOE46sxwGDJBo9qZ$31780cf2896878940669b4d57e1e1adb3701de5a71e8e8dc59d17445008a439911b5b1f640a769fc109b585b3bc3a2cb780572017899395a7444a9b9831724a3',
        ),
    ]

    for full_name, email, phone, password_hash in users:
        cursor.execute(
            """
            INSERT INTO users (full_name, email, phone, password_hash, is_verified)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                phone = VALUES(phone),
                password_hash = VALUES(password_hash),
                is_verified = TRUE
            """,
            (full_name, email, phone, password_hash)
        )

    cursor.execute(
        """
        INSERT IGNORE INTO friends (user_id, friend_id, status)
        SELECT john.id, bipin.id, 'accepted'
        FROM users john
        JOIN users bipin
          ON john.email = 'john.doe@example.com'
         AND bipin.email = 'bipin@example.com'
        """
    )

    restaurants = [
        ('Himalayan Java Coffee', 'Tridevi Marg, Thamel', 27.7153, 85.3123, 'Cafe', 'Coffee', 'mid', 4.6, 128, 'casual', '07:00:00', '21:00:00'),
        ('Bhojan Griha', 'Dillibazar, Kathmandu', 27.7070, 85.3283, 'Restaurant', 'Nepali', 'mid', 4.5, 94, 'family_friendly', '11:00:00', '22:00:00'),
        ('Roadhouse Cafe', 'Bhatbhateni, Kathmandu', 27.7219, 85.3302, 'Restaurant', 'Italian', 'mid', 4.4, 151, 'casual', '10:00:00', '22:30:00'),
        ('OR2K', 'Mandala Street, Thamel', 27.7150, 85.3119, 'Restaurant', 'Mediterranean', 'mid', 4.3, 212, 'casual', '09:00:00', '22:00:00'),
        ('Krishnarpan', 'Battisputali, Kathmandu', 27.7045, 85.3490, 'Restaurant', 'Nepali', 'expensive', 4.8, 76, 'fine_dining', '18:00:00', '22:00:00'),
        ('Korean Kitchen Picnic', 'Jhamsikhel, Lalitpur', 27.6762, 85.3159, 'Restaurant', 'Korean', 'mid', 4.2, 88, 'casual', '10:30:00', '21:30:00'),
    ]

    for row in restaurants:
        cursor.execute("SELECT id FROM restaurants WHERE name = %s LIMIT 1", (row[0],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE restaurants
                SET address = %s,
                    latitude = %s,
                    longitude = %s,
                    category = %s,
                    cuisine = %s,
                    price_range = %s,
                    rating = %s,
                    review_count = %s,
                    ambience = %s,
                    opening_time = %s,
                    closing_time = %s,
                    is_active = TRUE
                WHERE id = %s
                """,
                (*row[1:], existing['id'])
            )
        else:
            cursor.execute(
                """
                INSERT INTO restaurants
                    (name, address, latitude, longitude, category, cuisine,
                     price_range, rating, review_count, ambience,
                     opening_time, closing_time, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                row
            )
