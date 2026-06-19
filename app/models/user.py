from app.database import execute_query
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

class User:
    def __init__(self, id=None, full_name=None, email=None, phone=None, password=None, **kwargs):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.password = password
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    @staticmethod
    def create(full_name, email, phone, password):
        password_hash = generate_password_hash(password)
        verification_token = secrets.token_urlsafe(32)
        token_expiry = datetime.now() + timedelta(hours=24)
        query = """
            INSERT INTO users
                (full_name, email, phone, password_hash,
                 verification_token, verification_token_expiry)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (full_name, email, phone, password_hash,
                                     verification_token, token_expiry))

    @classmethod
    def get_by_id(cls, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        results = execute_query(query, (user_id,), fetch=True)
        if results:
            return cls(**results[0])
        return None

    @classmethod
    def get_by_email(cls, email):
        query = "SELECT * FROM users WHERE email = %s"
        results = execute_query(query, (email,), fetch=True)
        if results:
            return cls(**results[0])
        return None

    @staticmethod
    def get_by_verification_token(token):
        # Enforce the 24h expiry promised in the verification email. Rows
        # predating the expiry column (NULL) are treated as still valid so
        # existing unverified users are not locked out.
        query = """
            SELECT * FROM users
            WHERE verification_token = %s
              AND (verification_token_expiry IS NULL
                   OR verification_token_expiry > %s)
        """
        results = execute_query(query, (token, datetime.now()), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_reset_token(token):
        query = """
            SELECT * FROM users
            WHERE reset_token = %s AND reset_token_expiry > %s
        """
        results = execute_query(query, (token, datetime.now()), fetch=True)
        return results[0] if results else None

    @staticmethod
    def verify_email(user_id):
        query = """
            UPDATE users
            SET is_verified = TRUE, verification_token = NULL
            WHERE id = %s
        """
        return execute_query(query, (user_id,))

    @staticmethod
    def update_profile(user_id, full_name, phone, budget_preference,
                       cuisine_preference, transport_preference):
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
        query = "UPDATE users SET profile_pic = %s WHERE id = %s"
        return execute_query(query, (filename, user_id))

    @staticmethod
    def update_preferences(user_id, theme, language):
        query = """
            UPDATE users SET theme_preference=%s, language_preference=%s
            WHERE id = %s
        """
        return execute_query(query, (theme, language, user_id))

    @staticmethod
    def update_location(user_id, latitude, longitude):
        query = "UPDATE users SET latitude=%s, longitude=%s WHERE id = %s"
        return execute_query(query, (latitude, longitude, user_id))

    @staticmethod
    def set_reset_token(user_id):
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
        password_hash = generate_password_hash(new_password)
        query = """
            UPDATE users
            SET password_hash=%s, reset_token=NULL, reset_token_expiry=NULL
            WHERE id = %s
        """
        return execute_query(query, (password_hash, user_id))

    @staticmethod
    def check_password(stored_hash, password):
        return check_password_hash(stored_hash, password)

    @staticmethod
    def email_exists(email):
        query = "SELECT id FROM users WHERE email = %s"
        results = execute_query(query, (email,), fetch=True)
        return bool(results)

    def save(self):
        query = """
            INSERT INTO users (full_name, email, password)
            VALUES (%s, %s, %s)
        """
        return execute_query(query, (self.full_name, self.email, self.password))

    def update_profile_instance(self):
        query = """
            UPDATE users
            SET full_name = %s
            WHERE id = %s
        """
        return execute_query(query, (self.full_name, self.id))

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone
        }
