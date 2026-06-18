from flask import Blueprint
from app.controllers.notification_controller import (
    safety, add_contact, delete_contact,
    trigger_sos, cancel_sos,
    notifications, get_unread_count,
    mark_read, delete_notification,
    clear_all_notifications,
    update_notification_preferences
)

notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

# Emergency
notification_bp.add_url_rule('/safety',
    'safety', safety)
notification_bp.add_url_rule('/add-contact',
    'add_contact', add_contact, methods=['POST'])
notification_bp.add_url_rule('/delete-contact/<int:contact_id>',
    'delete_contact', delete_contact)
notification_bp.add_url_rule('/trigger-sos',
    'trigger_sos', trigger_sos, methods=['POST'])
notification_bp.add_url_rule('/cancel-sos',
    'cancel_sos', cancel_sos, methods=['POST'])

# Notifications
notification_bp.add_url_rule('/unread-count',
    'unread_count', get_unread_count)
notification_bp.add_url_rule('/mark-read/<int:notification_id>',
    'mark_read', mark_read, methods=['POST'])
notification_bp.add_url_rule('/delete/<int:notification_id>',
    'delete_notification', delete_notification)
notification_bp.add_url_rule('/clear-all',
    'clear_all', clear_all_notifications)
notification_bp.add_url_rule('/preferences',
    'update_preferences', update_notification_preferences, methods=['POST'])