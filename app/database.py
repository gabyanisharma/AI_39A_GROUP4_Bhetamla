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


def _table_exists(cursor, table):
    cursor.execute("SHOW TABLES LIKE %s", (table,))
    return cursor.fetchone() is not None


def _index_exists(cursor, table, index_name):
    cursor.execute("SHOW INDEX FROM `{}` WHERE Key_name = %s".format(table), (index_name,))
    return cursor.fetchone() is not None


def _ensure_column(cursor, table, column, definition):
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {definition}")


def _ensure_index(cursor, table, index_name, definition):
    if _table_exists(cursor, table) and not _index_exists(cursor, table, index_name):
        cursor.execute(f"ALTER TABLE `{table}` ADD {definition}")


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
    _ensure_column(cursor, 'restaurants', 'description', "description TEXT NULL")
    _ensure_column(cursor, 'restaurants', 'avg_cost_per_person', "avg_cost_per_person DECIMAL(10,2) NULL")
    _ensure_column(cursor, 'restaurants', 'thumbnail_url', "thumbnail_url VARCHAR(255) NULL")
    _ensure_column(cursor, 'notifications', 'read_at', "read_at TIMESTAMP NULL")
    _ensure_column(cursor, 'notifications', 'link', "link VARCHAR(255) NULL")
    _ensure_index(cursor, 'fare_alert', 'idx_fare_alert_user', "INDEX idx_fare_alert_user (userID, isActive)")
    _ensure_index(cursor, 'fare_history', 'idx_fare_history_meetup', "INDEX idx_fare_history_meetup (meetupID, mode, recordedAt)")


def _seed_demo_data(cursor):
    users = [
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
        """
    )

    restaurants = [
        ('Himalayan Java Coffee', 'Tridevi Marg, Thamel', 27.7153, 85.3123, 'Cafe', 'Coffee', 'mid', 4.6, 128, 'casual', '07:00:00', '21:00:00', 'Reliable coffee spot for study sessions and casual meetups.', 650),
        ('Bhojan Griha', 'Dillibazar, Kathmandu', 27.7070, 85.3283, 'Restaurant', 'Nepali', 'mid', 4.5, 94, 'family_friendly', '11:00:00', '22:00:00', 'Traditional Nepali dining in a restored heritage building.', 1200),
        ('Roadhouse Cafe', 'Bhatbhateni, Kathmandu', 27.7219, 85.3302, 'Restaurant', 'Italian', 'mid', 4.4, 151, 'casual', '10:00:00', '22:30:00', 'Pizza, pasta, and easy group seating near Bhatbhateni.', 1100),
        ('OR2K', 'Mandala Street, Thamel', 27.7150, 85.3119, 'Restaurant', 'Mediterranean', 'mid', 4.3, 212, 'casual', '09:00:00', '22:00:00', 'Vegetarian-friendly Thamel favorite with relaxed seating.', 950),
        ('Krishnarpan', 'Battisputali, Kathmandu', 27.7045, 85.3490, 'Restaurant', 'Nepali', 'expensive', 4.8, 76, 'fine_dining', '18:00:00', '22:00:00', 'Premium Nepali tasting-menu experience for special plans.', 3500),
        ('Korean Kitchen Picnic', 'Jhamsikhel, Lalitpur', 27.6762, 85.3159, 'Restaurant', 'Korean', 'mid', 4.2, 88, 'casual', '10:30:00', '21:30:00', 'Comfortable Korean restaurant for small groups.', 1000),
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
                    description = %s,
                    avg_cost_per_person = %s,
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
                     opening_time, closing_time, description,
                     avg_cost_per_person, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                row
            )
