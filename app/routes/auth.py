from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.controller.auth import AuthController
from app.controller.dashb import DashboardController


class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.auth_controller = AuthController()
        self.dashboard_controller = DashboardController()

    def register_routes(self):
        self.bp.add_url_rule("/", view_func=self.home)
        self.bp.add_url_rule("/about", view_func=self.about)
        self.bp.add_url_rule("/services", view_func=self.services)
        self.bp.add_url_rule("/contact", view_func=self.contact, methods=["GET", "POST"])
        self.bp.add_url_rule("/blog", view_func=self.blog)
        self.bp.add_url_rule("/gallery", view_func=self.gallery)
        self.bp.add_url_rule(
            "/login",
            view_func=self.auth_controller.login,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/register",
            view_func=self.auth_controller.register,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/forgot-password",
            view_func=self.auth_controller.forgot_password,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule("/logout", view_func=self.auth_controller.logout, methods=["POST"])
        self.bp.add_url_rule(
            "/dashboard",
            endpoint="dashboard",
            view_func=self.dashboard_controller.index,
        )
        return self.bp

    def home(self):
        return render_template("home.html")

    def about(self):
        return render_template("about.html")

    def services(self):
        return render_template("services.html")

    def contact(self):
        if request.method == "POST":
            fields = {
                "name": request.form.get("name", "").strip(),
                "email": request.form.get("email", "").strip(),
                "subject": request.form.get("subject", "").strip(),
                "message": request.form.get("message", "").strip(),
            }

            if not all(fields.values()):
                flash("Please complete every required field before sending.", "danger")
            else:
                flash(
                    "Thanks for reaching out. Your message passed validation and is ready "
                    "for a backend integration when you add one.",
                    "success",
                )
                return redirect(url_for("auth.contact"))

        return render_template("contact.html")

    def blog(self):
        return render_template("blog.html")

    def gallery(self):
        return render_template("gallery.html")
