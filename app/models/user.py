from app.database import execute_query
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

class User:

    # ─── CREATE ───────────────────────────────────────────────
    @staticmethod
    def create(full_name, email, phone, password):
        """Register a new user. Returns new user id or None."""
        password_hash = generate_password_hash(password)
        verification_token = secrets.token_urlsafe(32)

        query = """
            INSERT INTO users (full_name, email, phone, password_hash, verification_token)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (full_name, email, phone, password_hash, verification_token))

    # ─── READ ─────────────────────────────────────────────────
    @staticmethod
    def get_by_id(user_id):
        """Fetch a single user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        results = execute_query(query, (user_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_email(email):
        """Fetch a single user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        results = execute_query(query, (email,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_verification_token(token):
        """Fetch user by email verification token."""
        query = "SELECT * FROM users WHERE verification_token = %s"
        results = execute_query(query, (token,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_reset_token(token):
        """Fetch user by password reset token (only if not expired)."""
        query = """
            SELECT * FROM users
            WHERE reset_token = %s AND reset_token_expiry > %s
        """
        results = execute_query(query, (token, datetime.now()), fetch=True)
        return results[0] if results else None

    # ─── UPDATE ───────────────────────────────────────────────
    @staticmethod
    def verify_email(user_id):
        """Mark user as verified and clear the token."""
        query = """
            UPDATE users
            SET is_verified = TRUE, verification_token = NULL
            WHERE id = %s
        """
        return execute_query(query, (user_id,))

    @staticmethod
    def update_profile(user_id, full_name, phone, budget_preference,
                       cuisine_preference, transport_preference):
        """Update basic profile fields."""
        query = """
            UPDATE users
            SET full_name=%s, phone=%s, budget_preference=%s,
                cuisine_preference=%s, transport_preference=%s
            WHERE id = %s
        """
        return execute_query(query, (full_name, phone, budget_preference,
                                     cuisine_preference, transport_preference,
                                     user_id))

    @staticmethod
    def update_profile_pic(user_id, filename):
        """Update profile picture filename."""
        query = "UPDATE users SET profile_pic = %s WHERE id = %s"
        return execute_query(query, (filename, user_id))

    @staticmethod
    def update_preferences(user_id, theme, language):
        """Save theme and language preference."""
        query = """
            UPDATE users SET theme_preference=%s, language_preference=%s
            WHERE id = %s
        """
        return execute_query(query, (theme, language, user_id))

    @staticmethod
    def update_location(user_id, latitude, longitude):
        """Save user's last known location."""
        query = "UPDATE users SET latitude=%s, longitude=%s WHERE id = %s"
        return execute_query(query, (latitude, longitude, user_id))

    @staticmethod
    def set_reset_token(user_id):
        """Generate a password reset token valid for 24 hours."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=24)
        query = """
            UPDATE users SET reset_token=%s, reset_token_expiry=%s
            WHERE id = %s
        """
        execute_query(query, (token, expiry, user_id))
        return token

    @staticmethod
    def reset_password(user_id, new_password):
        """Hash and save a new password, clear reset token."""
        password_hash = generate_password_hash(new_password)
        query = """
            UPDATE users
            SET password_hash=%s, reset_token=NULL, reset_token_expiry=NULL
            WHERE id = %s
        """
        return execute_query(query, (password_hash, user_id))

    # ─── HELPERS ──────────────────────────────────────────────
    @staticmethod
    def check_password(stored_hash, password):
        """Return True if password matches the stored hash."""
        return check_password_hash(stored_hash, password)

    @staticmethod
    def email_exists(email):
        """Return True if email is already registered."""
        query = "SELECT id FROM users WHERE email = %s"
        results = execute_query(query, (email,), fetch=True)
        return bool(results)