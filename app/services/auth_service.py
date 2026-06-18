from werkzeug.security import generate_password_hash, check_password_hash
from app.database_manager import DatabaseManager
from app.models.user import User
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger('auth_service')

class AuthService:
    def __init__(self):
        self.db = DatabaseManager()

    def register_user(self, full_name: str, email: str, password: str) -> Optional[int]:
        """Handles business logic for user registration."""
        logger.info(f"Attempting to register user: {email}")
        
        if User.get_by_email(email):
            logger.warning(f"Registration failed: Email {email} already exists.")
            return None

        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (full_name, email, password_hash) 
            VALUES (%s, %s, %s)
        """
        user_id = self.db.execute_query(query, (full_name, email, password_hash))
        
        if user_id:
            logger.info(f"User {email} registered successfully with ID {user_id}")
        return user_id

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Handles business logic for user login."""
        logger.info(f"Attempting authentication for: {email}")
        
        user_data = User.get_by_email(email)
        if not user_data:
            logger.warning(f"Login failed: User {email} not found.")
            return None

        if check_password_hash(user_data['password_hash'], password):
            logger.info(f"User {email} authenticated successfully.")
            return user_data
            
        logger.warning(f"Login failed: Incorrect password for {email}.")
        return None

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Hashes and updates the user's password."""
        password_hash = generate_password_hash(new_password)
        query = "UPDATE users SET password_hash = %s WHERE id = %s"
        result = self.db.execute_query(query, (password_hash, user_id))
        return result is not None