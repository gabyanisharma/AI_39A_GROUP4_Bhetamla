import sys
import os

# Ensure the app directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database_manager import DatabaseManager
from config import Config

def add_organizer_column():
    db = DatabaseManager()
    db_name = Config.MYSQL_DB

    # Check if column exists using INFORMATION_SCHEMA
    check_sql = """
        SELECT COUNT(*) as col_count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'meetups' 
        AND COLUMN_NAME = 'organizer_id'
    """
    
    try:
        # Perform the metadata check first to avoid MySQL syntax errors
        result = db.execute_query(check_sql, (db_name,), fetch=True)
        
        if result and result[0]['col_count'] == 0:
            print("Adding 'organizer_id' column to 'meetups' table...")
            alter_sql = "ALTER TABLE meetups ADD COLUMN organizer_id INT;"
            db.execute_query(alter_sql)
            print("✓ SUCCESS: 'organizer_id' column added successfully.")
        else:
            print("✓ INFO: 'organizer_id' column already exists in 'meetups' table.")
    except Exception as e:
        print(f"✗ ERROR: Failed to add 'organizer_id' column: {e}")

if __name__ == "__main__":
    add_organizer_column()