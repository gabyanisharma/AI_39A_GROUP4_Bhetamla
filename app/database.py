import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Create and return a new database connection."""
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """
    Run a SQL query.
    - fetch=False  → INSERT / UPDATE / DELETE  (returns lastrowid)
    - fetch=True   → SELECT  (returns list of dicts)
    """
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid

    except Error as e:
        print(f"Query error: {e}")
        connection.rollback()
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()