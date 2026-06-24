from flask import Blueprint
from app.controllers.auth_controller import (
    register, login, logout,
    verify_email, forgot_password, reset_password
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

auth_bp.add_url_rule('/register',        'register',        register,        methods=['GET', 'POST'])
auth_bp.add_url_rule('/login',           'login',           login,           methods=['GET', 'POST'])
auth_bp.add_url_rule('/logout',          'logout',          logout)
auth_bp.add_url_rule('/verify/<token>',  'verify_email',    verify_email)
auth_bp.add_url_rule('/forgot-password', 'forgot_password', forgot_password, methods=['GET', 'POST'])
auth_bp.add_url_rule('/reset/<token>',   'reset_password',  reset_password,  methods=['GET', 'POST'])
