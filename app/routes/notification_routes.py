from flask import Blueprint
from app.controllers.notification_controller import (
    safety, add_contact, delete_contact,
    trigger_sos, cancel_sos
)

notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

notification_bp.add_url_rule('/safety',                   'safety',         safety)
notification_bp.add_url_rule('/add-contact',              'add_contact',    add_contact,    methods=['POST'])
notification_bp.add_url_rule('/delete-contact/<int:contact_id>', 'delete_contact', delete_contact)
notification_bp.add_url_rule('/trigger-sos',              'trigger_sos',    trigger_sos,    methods=['POST'])
notification_bp.add_url_rule('/cancel-sos',               'cancel_sos',     cancel_sos,     methods=['POST'])