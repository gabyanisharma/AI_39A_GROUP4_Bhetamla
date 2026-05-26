from mysql.connector import pooling, Error
from config import Config
import logging

class DatabaseManager:
    _instance = None
    _pool = None

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
            except Error as e:
                logging.error(f"Error creating connection pool: {e}")
        return cls._instance

    def get_connection(self):
        return self._pool.get_connection()

    def execute_query(self, query, params=(), fetch=False, commit=True):
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            if commit:
                connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            connection.close()