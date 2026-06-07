import pymysql
from config import Config
import logging

logger = logging.getLogger('database')

def get_db_connection():
    """Create MySQL database connection using pymysql."""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("[DB] MySQL connection successful (legacy wrapper)")
        return connection
    except Exception as e:
        logger.error(f"[DB] Connection error: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """
    Run a SQL query.
    - fetch=False  → INSERT / UPDATE / DELETE  (returns lastrowid)
    - fetch=True   → SELECT  (returns list of dicts)
    """
    connection = get_db_connection()
    if not connection:
        logger.error(f"[DB] execute_query failed: Could not establish connection")
        return None

    try:
        with connection.cursor() as cursor:
            logger.debug(f"[DB] Executing query: {query[:100]}...")
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                logger.debug(f"[DB] Query returned {len(result)} rows")
                return result
            else:
                connection.commit()
                last_id = cursor.lastrowid
                logger.info(f"[DB] Query executed successfully. Last row ID: {last_id}")
                return last_id
    except Exception as e:
        logger.error(f"[DB] Query error: {e}")
        connection.rollback()
        return None

    finally:
        if connection:
            connection.close()
