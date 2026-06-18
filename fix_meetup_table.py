import sys
import os

# Ensure the app directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database_manager import DatabaseManager

def fix_meetup():
    db = DatabaseManager()
    sql = "CREATE TABLE IF NOT EXISTS meetups (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, user_id INT, creator_id INT, status VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
    print("Creating 'meetups' table...")
    try:
        db.execute_query(sql)
        print("✓ SUCCESS: Meetups table created successfully!")
    except Exception as e:
        print(f"✗ ERROR: Failed to create table: {e}")

if __name__ == "__main__":
    fix_meetup()