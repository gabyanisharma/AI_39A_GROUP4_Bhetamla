from flask import flash, redirect, render_template, request, session, url_for

from app.modal.auth import AuthModel


def _password_is_valid(password):
    return (
        len(password) >= 8
        and any(char.islower() for char in password)
        and any(char.isupper() for char in password)
        and any(char.isdigit() for char in password)
    )


class AuthController:
    def __init__(self):
        self.auth_model = AuthModel()

    def _is_authenticated(self):
        return bool(session.get("user"))

    def _persist_user_session(self, user, remember):
        session.clear()
        session["user"] = user.public_profile()
        session.permanent = remember

    def login(self):
        if self._is_authenticated():
            return redirect(url_for("auth.dashboard"))

        if request.method == "POST":
            identifier = request.form.get("identifier", "")
            password = request.form.get("password", "")
            remember = request.form.get("remember") == "on"

            user = self.auth_model.authenticate(identifier, password)
            if user:
                self._persist_user_session(user, remember)
                flash(f"Welcome back, {user.full_name}.", "success")
                return redirect(url_for("auth.dashboard"))

            flash("Invalid email, username, or password.", "danger")

        return render_template(
            "login.html",
            demo_credentials=self.auth_model.get_demo_credentials(),
        )

    def register(self):
        if self._is_authenticated():
            return redirect(url_for("auth.dashboard"))

        if request.method == "POST":
            full_name = request.form.get("fullname", "")
            email = request.form.get("email", "")
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if password != confirm_password:
                flash("Your password confirmation does not match.", "danger")
            elif not request.form.get("terms"):
                flash("Please accept the terms before creating an account.", "danger")
            elif not _password_is_valid(password):
                flash(
                    "Use at least 8 characters with uppercase, lowercase, and a number.",
                    "danger",
                )
            else:
                try:
                    user = self.auth_model.register_user(full_name, username, email, password)
                except ValueError as error:
                    flash(str(error), "danger")
                else:
                    self._persist_user_session(user, remember=False)
                    flash("Account created successfully.", "success")
                    return redirect(url_for("auth.dashboard"))

        return render_template("register.html")

    def forgot_password(self):
        if request.method == "POST":
            email = request.form.get("email", "")
            if not email.strip():
                flash("Enter the email address linked to your account.", "warning")
            else:
                self.auth_model.request_password_reset(email)
                flash(
                    "If that email exists, reset instructions are ready to be sent. "
                    "This demo keeps everything local, so no message was dispatched.",
                    "info",
                )
                return redirect(url_for("auth.forgot_password"))

        return render_template("forgot_password.html")

    def logout(self):
        if session.get("user"):
            session.clear()
            flash("You have been signed out.", "info")

        return redirect(url_for("auth.login"))
