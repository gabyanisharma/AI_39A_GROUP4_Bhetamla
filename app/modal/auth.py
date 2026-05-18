from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash


_DEMO_EMAIL = "demo@bhetam.com"
_DEMO_PASSWORD = "Password123"

_USER_STORE = {}
_USERNAME_INDEX = {}


@dataclass(frozen=True)
class User:
    full_name: str
    username: str
    email: str
    password_hash: str

    def public_profile(self):
        return {
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
        }


def reset_auth_state():
    _USER_STORE.clear()
    _USERNAME_INDEX.clear()

    demo_user = User(
        full_name="Demo User",
        username="demo",
        email=_DEMO_EMAIL,
        password_hash=generate_password_hash(_DEMO_PASSWORD),
    )
    _USER_STORE[demo_user.email] = demo_user
    _USERNAME_INDEX[demo_user.username] = demo_user.email


reset_auth_state()


class AuthModel:
    def authenticate(self, identifier, password):
        normalized_identifier = identifier.strip().lower()
        email = _USERNAME_INDEX.get(normalized_identifier, normalized_identifier)
        user = _USER_STORE.get(email)

        if not user or not check_password_hash(user.password_hash, password):
            return None

        return user

    def register_user(self, full_name, username, email, password):
        normalized_full_name = " ".join(full_name.split())
        normalized_username = username.strip().lower()
        normalized_email = email.strip().lower()

        if not normalized_full_name or not normalized_username or not normalized_email or not password:
            raise ValueError("All registration fields are required.")

        if normalized_email in _USER_STORE:
            raise ValueError("An account with that email already exists.")

        if normalized_username in _USERNAME_INDEX:
            raise ValueError("That username is already in use.")

        user = User(
            full_name=normalized_full_name,
            username=normalized_username,
            email=normalized_email,
            password_hash=generate_password_hash(password),
        )

        _USER_STORE[normalized_email] = user
        _USERNAME_INDEX[normalized_username] = normalized_email
        return user

    def request_password_reset(self, email):
        normalized_email = email.strip().lower()
        return normalized_email in _USER_STORE

    def get_demo_credentials(self):
        return {"email": _DEMO_EMAIL, "password": _DEMO_PASSWORD}
