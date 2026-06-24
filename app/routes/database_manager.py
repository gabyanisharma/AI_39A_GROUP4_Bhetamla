import mysql.connector
from mysql.connector import pooling, Error
from config import Config
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger('database_manager')

class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[pooling.MySQLConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="bhetamla_pool",
                    pool_size=5,
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB
                )
                logger.info("Database connection pool created successfully.")
            except Error as e:
                logger.error(f"Error creating connection pool: {e}")
        return cls._instance

    def get_connection(self):
        return self._pool.get_connection()

    def execute_query(self, query: str, params: Tuple = (), fetch: bool = False, commit: bool = True) -> Any:
        """
        Executes a SQL query with proper error handling and connection management.
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
                return result
            
            if commit:
                connection.commit()
            
            return cursor.lastrowid if cursor.rowcount > 0 else None

        except Error as e:
            logger.error(f"Database Query Error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def transaction(self, queries: List[Tuple[str, Tuple]]) -> bool:
        """Executes multiple queries in a single transaction."""
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            connection.start_transaction()
            for query, params in queries:
                cursor.execute(query, params)
            connection.commit()
            return True
        except Error as e:
            logger.error(f"Transaction failed: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()