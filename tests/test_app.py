import unittest

from app import create_app
from app.modal.auth import reset_auth_state


class AppTests(unittest.TestCase):
    def setUp(self):
        reset_auth_state()
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
        self.client = self.app.test_client()

    def test_public_pages_render(self):
        for path in [
            "/",
            "/about",
            "/services",
            "/contact",
            "/blog",
            "/gallery",
            "/login",
            "/register",
            "/forgot-password",
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_demo_user_can_log_in(self):
        response = self.client.post(
            "/login",
            data={"identifier": "demo@bhetam.com", "password": "Password123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back, Demo User.", response.data)
        self.assertIn(b"Delivery overview", response.data)

    def test_registration_creates_account_and_loads_dashboard(self):
        response = self.client.post(
            "/register",
            data={
                "fullname": "Alex Rana",
                "email": "alex@example.com",
                "username": "alex",
                "password": "StrongPass1",
                "confirm_password": "StrongPass1",
                "terms": "on",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created successfully.", response.data)
        self.assertIn(b"Welcome, Alex Rana.", response.data)

    def test_contact_submission_shows_confirmation(self):
        response = self.client.post(
            "/contact",
            data={
                "name": "Priya",
                "email": "priya@example.com",
                "subject": "Workflow question",
                "message": "Can Bhetam support weekly executive status notes?",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Thanks for reaching out.", response.data)


if __name__ == "__main__":
    unittest.main()
