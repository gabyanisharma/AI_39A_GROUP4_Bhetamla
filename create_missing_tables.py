import sys
import os
import logging

# Ensure the app directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('table_repair')

# Definitions sourced from setup_database.py
REPAIR_SQL = {
    'places': """
    CREATE TABLE IF NOT EXISTS places (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        rating FLOAT,
        review_count INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'meetups': """
    CREATE TABLE IF NOT EXISTS meetups (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        organizer_id INT NOT NULL,
        scheduled_time DATETIME,
        midpoint_latitude DECIMAL(10, 8),
        midpoint_longitude DECIMAL(11, 8),
        meeting_place_id INT,
        status VARCHAR(50) DEFAULT 'upcoming',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (meeting_place_id) REFERENCES places(id),
        INDEX idx_organizer_id (organizer_id),
        INDEX idx_scheduled_time (scheduled_time)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    'emergency_contacts': """
    CREATE TABLE IF NOT EXISTS emergency_contacts (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        relationship VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
}

def repair():
    logger.info("Starting database table repair...")
    db = DatabaseManager()
    
    for table_name, sql in REPAIR_SQL.items():
        logger.info(f"Checking table: {table_name}")
        try:
            # Ensure we use the shared execute_query logic
            result = db.execute_query(sql)
            logger.info(f"✓ Table '{table_name}' is now ready.")
        except Exception as e:
            if "already exists" in str(e): continue
            logger.error(f"✗ Failed to create/check table '{table_name}': {e}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  BHETAMLA MISSING TABLES REPAIR")
    print("="*50)
    repair()
    print("="*50 + "\n")