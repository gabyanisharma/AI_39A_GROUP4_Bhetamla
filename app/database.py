import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

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
    try:
        create_database_if_not_exists()
    except Exception as e:
        # Likely a connection/auth error - warn and skip DB initialization so app can start.
        print("Warning: could not connect to MySQL to initialize database:", str(e))
        print("If you intend to use MySQL, verify MYSQL_HOST, MYSQL_USER and MYSQL_PASSWORD in config.py or .env.")
        return

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
            _ensure_group_features_schema(cursor)
            _seed_achievements(cursor)
            _seed_demo_data(cursor)
            _seed_trending_spots(cursor)
            _seed_kathmandu_restaurants(cursor)   # also calls _seed_kathmandu_offers
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
    _ensure_column(cursor, 'emergency_contacts', 'email', "email VARCHAR(255) NULL")
    _ensure_column(cursor, 'users', 'verification_token_expiry', "verification_token_expiry DATETIME NULL")
    _ensure_column(cursor, 'venue_votes', 'restart_count', "restart_count INT DEFAULT 0")
    _ensure_column(cursor, 'meetups', 'invite_code', "invite_code VARCHAR(32) NULL")
    try:
        cursor.execute("ALTER TABLE meetups ADD UNIQUE KEY unique_invite_code (invite_code)")
    except Exception:
        pass
    # Users who left a meetup chat: excluded from membership re-sync.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chat_optout (
            group_id INT NOT NULL,
            user_id INT NOT NULL,
            left_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES friend_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
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
    _ensure_index(cursor, 'trending_spots', 'idx_trending_spots_feed', "INDEX idx_trending_spots_feed (is_active, trend_score)")
    _ensure_index(cursor, 'user_spot_interactions', 'idx_spot_interactions_spot', "INDEX idx_spot_interactions_spot (spot_id, interaction_type)")
    _ensure_index(cursor, 'spot_recommendations', 'idx_spot_recommendations_user', "INDEX idx_spot_recommendations_user (user_id, is_dismissed)")
    _ensure_index(cursor, 'notifications', 'idx_notifications_user_read', "INDEX idx_notifications_user_read (user_id, is_read)")
    _ensure_index(cursor, 'smart_alert_log', 'idx_smart_alert_user', "INDEX idx_smart_alert_user (user_id, alert_key)")
    _ensure_column(cursor, 'friend_groups', 'is_chat_group',
                   "is_chat_group BOOLEAN DEFAULT FALSE")
    _ensure_column(cursor, 'meetup_members', 'hidden_from_groups',
                   "hidden_from_groups BOOLEAN DEFAULT FALSE")
    _ensure_column(cursor, 'meetups', 'winning_restaurant_id',
                   "winning_restaurant_id INT NULL")
    _ensure_column(cursor, 'meetups', 'winning_venue_name',
                   "winning_venue_name VARCHAR(255) NULL")
    _ensure_column(cursor, 'user_saved_offers', 'notified',
                   "notified TINYINT(1) NOT NULL DEFAULT 0")

    # Idempotency constraints — prevent re-seeding from duplicating rows
    # on databases created before these UNIQUE keys were added.
    try:
        cursor.execute(
            "ALTER TABLE restaurants ADD UNIQUE KEY uq_restaurant_name (name)"
        )
    except Exception:
        pass  # key already exists
    try:
        cursor.execute(
            "ALTER TABLE restaurant_offers ADD UNIQUE KEY uq_offer_restaurant_title (restaurant_id, title)"
        )
    except Exception:
        pass  # key already exists


def _ensure_group_features_schema(cursor):
    """Tables for group vote, gallery, chat, and achievements."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venue_votes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            meetup_id INT NOT NULL,
            created_by INT NOT NULL,
            deadline DATETIME NOT NULL,
            status ENUM('open', 'closed') DEFAULT 'open',
            winner_option_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venue_vote_options (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vote_id INT NOT NULL,
            restaurant_id INT NULL,
            label VARCHAR(255) NOT NULL,
            address VARCHAR(255),
            FOREIGN KEY (vote_id) REFERENCES venue_votes(id) ON DELETE CASCADE,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venue_vote_casts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vote_id INT NOT NULL,
            option_id INT NOT NULL,
            user_id INT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vote_id) REFERENCES venue_votes(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES venue_vote_options(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_vote_user (vote_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetup_gallery (
            id INT AUTO_INCREMENT PRIMARY KEY,
            meetup_id INT NOT NULL,
            user_id INT NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            caption VARCHAR(500),
            is_public BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery_likes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            gallery_id INT NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (gallery_id) REFERENCES meetup_gallery(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_gallery_like (gallery_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            gallery_id INT NOT NULL,
            user_id INT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (gallery_id) REFERENCES meetup_gallery(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            owner_id INT NOT NULL,
            is_chat_group BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_group_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT NOT NULL,
            user_id INT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES friend_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_group_member (group_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chat_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT NOT NULL,
            user_id INT NOT NULL,
            body TEXT NOT NULL,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES friend_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chat_reads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message_id INT NOT NULL,
            user_id INT NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES group_chat_messages(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_message_read (message_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chat_typing (
            group_id INT NOT NULL,
            user_id INT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES friend_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unlock_key VARCHAR(50) NOT NULL UNIQUE,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            badge_icon VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            achievement_id INT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_split_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            meetup_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE
        )
    """)
    try:
        cursor.execute("""
            ALTER TABLE notifications
            MODIFY type ENUM(
                'meetup','friend','reminder','sos','general',
                'vote','gallery','chat','achievement'
            ) DEFAULT 'general'
        """)
    except Exception:
        pass


ACHIEVEMENTS_SEED = [
    ('first_contact', 'First Contact',
     'Created or joined your very first meetup.', 'first_contact.png'),
    ('road_tripper', 'Road Tripper',
     'Successfully completed 5 meetups.', 'road_tripper.png'),
    ('penny_pincher', 'Penny Pincher',
     'Used the Budget Split feature to settle ride costs.', 'penny_pincher.png'),
    ('democratic_leader', 'Democratic Leader',
     'Created a Group Voting poll in a meetup.', 'democratic_leader.png'),
    ('lifeline', 'Lifeline',
     'Set up your Emergency Alerts or emergency contacts profile.', 'lifeline.png'),
    ('social_butterfly', 'Social Butterfly',
     'Sent your first message in a meetup group chat.', 'social_butterfly.png'),
    ('reliable_rider', 'Reliable Rider',
     'Attended 3 consecutive meetups successfully.', 'reliable_rider.png'),
]


def _seed_achievements(cursor):
    for unlock_key, title, description, badge_icon in ACHIEVEMENTS_SEED:
        cursor.execute(
            """
            INSERT INTO achievements (unlock_key, title, description, badge_icon)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                badge_icon = VALUES(badge_icon)
            """,
            (unlock_key, title, description, badge_icon)
        )


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


def _seed_trending_spots(cursor):
    """Seed curated spots for the Explore feed of trending meetup spots."""
    # Updated structure: added thumbnail_url and image_url at the end of each tuple
    spots = [
        ('The Old House', 'Riverside lounge with live music and a relaxed deck — a weekend favourite.',
         'Jhamsikhel, Lalitpur', 27.6745, 85.3120, 'Lounge', 'Continental', 'lively',
         'expensive', 1800, 4.7, 240, 92.5, True, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAHu8fHIhqb55609GUE-BsrQRfd638DKWpWU_0VIqrcN2858XtfzdwI56HaIbxEKIt3XzqBBw99xZNUW10vjFl85FvrTCbpmC8r2aQbJzLxPRLJa8uSJxglnulONZg21p1bb8mijYKpXthXi=w408-h612-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Cafe Soma', 'Garden cafe tucked in Patan, great for long catch-ups over coffee.',
         'Pulchowk, Lalitpur', 27.6790, 85.3170, 'Cafe', 'Cafe', 'cozy',
         'mid', 700, 4.6, 188, 81.0, True, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAFWul88CltKO0LNQvjeEUkIRWS2HQIFXXxETQ6VyCD2lRrxPDX9qZFdG_PcXuxVAPQ1I4duFiDPZyPrAj_GsmI3NajSFt6YYEzFeJQuMA8B4ohvhSeAuruGuOimg2suPOmsStPT=w408-h306-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Trisara', 'Open-air Newari courtyard restaurant buzzing on weekend evenings.',
         'Lazimpat, Kathmandu', 27.7220, 85.3210, 'Restaurant', 'Nepali', 'lively',
         'mid', 1300, 4.5, 165, 76.0, True, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAFODU5YtglcmcKqdMdWGbHXUdgu83A0bAVO5dVnZLfmjHoLu45aAOMECHLe4sRQSF6V4D3xn0fMiXtuhorZoAcyOGe6LO3q8M1hzA0A4Nf2BQjvhmEx6pEA0PWcYjhxUZGdQT_0Dp2vuOY=w408-h306-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Places Restaurant & Bar', 'Rooftop spot with skyline views popular for group hangouts.',
         'Thamel, Kathmandu', 27.7160, 85.3110, 'Restaurant', 'Continental', 'lively',
         'mid', 1100, 4.4, 142, 70.0, False, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAFaWzhjNqvysUQBiT7y0A7KvnMT_l9IJfawTWECjbchj6P7JuCk0I-7G_Ka_-sQEKY55Ua4AcVlqS0hP06-mzfzH8CH5ZVOwp72VYGQswVwubuRv_x4Xaohx7tTCKdMrYD4UZDZ=w408-h306-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Karma Coffee', 'Specialty coffee roaster — quiet, laptop-friendly mornings.',
         'Jhamsikhel, Lalitpur', 27.6758, 85.3142, 'Cafe', 'Cafe', 'quiet',
         'budget', 450, 4.5, 121, 64.0, False, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAGU3HxUyIZS4O7PjbbyMVGEiW9ezmc7_JWyuROgPhSqTXKnkCt195gaxnY3hJrhN866VzclDONeoTCeVdbwke0Od_ItkKrcv9bbhFWyV8ETaF5k3VtTSev2MGZ8qRxyGFcXi8D3QA=w408-h305-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Or2K Rooftop', 'Cushioned rooftop seating, vegetarian mezze, and a chill crowd.',
         'Mandala Street, Thamel', 27.7152, 85.3119, 'Restaurant', 'Mediterranean', 'cozy',
         'mid', 950, 4.3, 207, 58.0, False, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAEtE8_2E175kqPs8uLDtt11pblxc8OLiygAwJYtrQmv6EGEu_hfhBnIriZXAu9Q3WLqQ4lLcMxvfuMkByGW8XcRBuzQAaEW3XgXrSsPLnVDz5E47KXaLJsB6DaR8styUNY5-A4sVg=w408-h544-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Le Sherpa', 'Farm-to-table garden venue, weekend farmers market draws crowds.',
         'Maharajgunj, Kathmandu', 27.7380, 85.3290, 'Restaurant', 'Continental', 'cozy',
         'expensive', 2000, 4.6, 134, 55.0, False, 'https://lh3.googleusercontent.com/gps-cs-s/APNQkAEdxpg--l_2M9g76nR03Swhc-TV5dDbhDkhJan74I0d7qNyw48s4aVuG8RnLnjxO12ypPY5l8QJ0expnpRfBmv2Vf_vd9kvmMzy4ciHKnrekgxph6ojW9LhSVxnr9GlwkU_j2T9=w408-h272-k-no', 'https://link-to-your-large-image.jpg'),
         
        ('Himalayan Java Durbar Marg', 'Flagship cafe, central meeting point in the heart of the city.',
         'Durbar Marg, Kathmandu', 27.7110, 85.3180, 'Cafe', 'Coffee', 'lively',
         'mid', 650, 4.4, 312, 51.0, False, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHMQnicvuyj8xjtnebiJnGnVq-bBsP2WvAeFJ_EfeP1Mb92GLfReSMXLo&s=10', 'https://link-to-your-large-image.jpg'),
    ]
 
    for row in spots:
        cursor.execute("SELECT id FROM trending_spots WHERE name = %s LIMIT 1", (row[0],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE trending_spots
                SET description = %s, address = %s, latitude = %s, longitude = %s,
                    category = %s, cuisine = %s, ambience = %s, price_range = %s,
                    avg_cost_per_person = %s, rating = %s, review_count = %s,
                    trend_score = %s, is_featured = %s, thumbnail_url = %s, image_url = %s, is_active = TRUE
                WHERE id = %s
                """,
                (*row[1:], existing['id'])
            )
        else:
            cursor.execute(
                """
                INSERT INTO trending_spots
                    (name, description, address, latitude, longitude, category,
                     cuisine, ambience, price_range, avg_cost_per_person, rating,
                     review_count, trend_score, is_featured, thumbnail_url, image_url, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                row
            )


def _seed_kathmandu_restaurants(cursor):
    """Seed ~100 real Kathmandu Valley restaurants so every fresh install
    has a rich dataset for Browse Restaurants and nearby-venue features."""
    try:
        from app.data.kathmandu_restaurants import KATHMANDU_RESTAURANTS
    except ImportError:
        return

    for row in KATHMANDU_RESTAURANTS:
        name = row[0]
        cursor.execute("SELECT id FROM restaurants WHERE name = %s LIMIT 1", (name,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                """
                INSERT INTO restaurants
                    (name, address, latitude, longitude, category, cuisine,
                     price_range, rating, review_count, ambience,
                     opening_time, closing_time, description,
                     avg_cost_per_person, is_active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, TRUE)
                """,
                row
            )

    # Seed offers linked to the restaurants above
    _seed_kathmandu_offers(cursor)


def _seed_kathmandu_offers(cursor):
    """Seed restaurant offers from KATHMANDU_OFFERS in the data file.

    Each offer is linked to its restaurant by name lookup.  Offers run for
    6 months from the current date so they are always 'active' on a fresh
    install. Already-existing rows (matched by restaurant_id + title) are
    skipped so re-running initialize_db() is safe.
    """
    try:
        from app.data.kathmandu_restaurants import KATHMANDU_OFFERS
    except ImportError:
        return

    import datetime
    today = datetime.date.today()
    valid_until = today + datetime.timedelta(days=180)

    for restaurant_name, title, description, discount_percent in KATHMANDU_OFFERS:
        # Resolve restaurant id by name (case-insensitive, trimmed)
        cursor.execute(
            "SELECT id FROM restaurants WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) LIMIT 1",
            (restaurant_name,)
        )
        row = cursor.fetchone()
        if not row:
            # Restaurant not seeded yet — skip silently
            continue
        restaurant_id = row['id']

        # Check for an existing identical offer to stay idempotent
        cursor.execute(
            """
            SELECT id FROM restaurant_offers
            WHERE restaurant_id = %s AND LOWER(TRIM(title)) = LOWER(TRIM(%s))
            LIMIT 1
            """,
            (restaurant_id, title)
        )
        if cursor.fetchone():
            continue

        cursor.execute(
            """
            INSERT INTO restaurant_offers
                (restaurant_id, title, description, discount_percent,
                 valid_from, valid_until, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """,
            (restaurant_id, title, description, discount_percent,
             today, valid_until)
        )


if __name__ == '__main__':
    initialize_db()
    print('Database initialized.')
