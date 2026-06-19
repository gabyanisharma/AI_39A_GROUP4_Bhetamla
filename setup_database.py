#!/usr/bin/env python3
"""
Database schema setup script for Bhetamla.
Run this to initialize the database structure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('db_setup')

# SQL statements to create the database and tables
SETUP_SQL = [
    # Create database
    f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}",
    
    # Use database
    f"USE {Config.MYSQL_DB}",
    
    # Create users table
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        phone VARCHAR(20),
        password VARCHAR(255) NOT NULL,
        is_verified BOOLEAN DEFAULT FALSE,
        verification_token VARCHAR(255),
        reset_token VARCHAR(255),
        reset_token_expiry DATETIME,
        theme_preference VARCHAR(20) DEFAULT 'light',
        language_preference VARCHAR(10) DEFAULT 'en',
        budget_preference VARCHAR(50),
        cuisine_preference VARCHAR(100),
        transport_preference VARCHAR(50),
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_verification_token (verification_token),
        INDEX idx_reset_token (reset_token)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    
    # Create places table
    """
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
    
    # Create meetups table
    """
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
    
    # Create meetup_participants table
    """
    CREATE TABLE IF NOT EXISTS meetup_participants (
        id INT PRIMARY KEY AUTO_INCREMENT,
        meetup_id INT NOT NULL,
        user_id INT NOT NULL,
        status VARCHAR(50) DEFAULT 'attending',
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY unique_participant (meetup_id, user_id),
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    
    # Create votes table
    """
    CREATE TABLE IF NOT EXISTS votes (
        id INT PRIMARY KEY AUTO_INCREMENT,
        meetup_id INT NOT NULL,
        user_id INT NOT NULL,
        place_id INT NOT NULL,
        voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (place_id) REFERENCES places(id),
        UNIQUE KEY unique_vote (meetup_id, user_id, place_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    
    # Create notifications table
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        type VARCHAR(50),
        message TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        related_meetup_id INT,
        related_user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (related_meetup_id) REFERENCES meetups(id) ON DELETE SET NULL,
        FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_is_read (is_read)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Create friends table
    """
    CREATE TABLE IF NOT EXISTS friends (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        friend_id INT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY unique_friendship (user_id, friend_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Create availability_slots table
    """
    CREATE TABLE IF NOT EXISTS availability_slots (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # Create schedule_invites table
    """
    CREATE TABLE IF NOT EXISTS schedule_invites (
        id INT PRIMARY KEY AUTO_INCREMENT,
        schedule_id INT NOT NULL,
        user_id INT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        FOREIGN KEY (schedule_id) REFERENCES meetups(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    
    # Create emergency_contacts table
    """
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
    """,
    
    # Create sos_alerts table
    """
    CREATE TABLE IF NOT EXISTS sos_alerts (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        message TEXT,
        cancel_pin VARCHAR(10),
        status VARCHAR(20) DEFAULT 'active',
        triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cancelled_at TIMESTAMP NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
]

def setup_database():
    """Execute database setup script."""
    try:
        logger.info(f"Connecting to MySQL at {Config.MYSQL_HOST} as {Config.MYSQL_USER}...")
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        
        if not connection.is_connected():
            logger.error("Failed to connect to MySQL")
            return False
        
        cursor = connection.cursor()
        logger.info("✓ Connected to MySQL successfully")
        
        for i, sql_statement in enumerate(SETUP_SQL, 1):
            try:
                # Split multiple statements and execute separately
                statements = [s.strip() for s in sql_statement.split(';') if s.strip()]
                for stmt in statements:
                    logger.info(f"[{i}/{len(SETUP_SQL)}] Executing: {stmt[:60]}...")
                    cursor.execute(stmt)
                    connection.commit()
                
            except Error as e:
                logger.error(f"Error executing statement {i}: {e}")
                connection.rollback()
                return False
        
        cursor.close()
        connection.close()
        
        logger.info("✓ Database setup completed successfully!")
        logger.info(f"✓ Database '{Config.MYSQL_DB}' is ready with all required tables")
        return True
        
    except Error as e:
        logger.error(f"MySQL error: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("1. Ensure MySQL is running: mysql.server status")
        logger.error(f"2. Check credentials in config.py:")
        logger.error(f"   - Host: {Config.MYSQL_HOST}")
        logger.error(f"   - User: {Config.MYSQL_USER}")
        logger.error(f"   - Password: [check config.py]")
        logger.error("3. If error is 'Access denied', update MYSQL_PASSWORD in config.py")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  BHETAMLA DATABASE SETUP")
    print("="*70)
    
    success = setup_database()
    
    print("\n" + "="*70)
    if success:
        print("  ✓ Database setup complete!")
        print("  Your application is ready to use.")
        print("="*70 + "\n")
        exit(0)
    else:
        print("  ✗ Database setup failed")
        print("  Please fix the errors above and try again.")
        print("="*70 + "\n")
        exit(1)
