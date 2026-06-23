import logging
import random
import string
from typing import Tuple, Dict, Any
from app.database_manager import DatabaseManager

logger = logging.getLogger('notification_service')

class NotificationService:
    def __init__(self):
        self.db = DatabaseManager()

    def trigger_sos(self, user_id: int, latitude: float, longitude: float, message: str) -> Tuple[int, str]:
        """
        Triggers a new SOS alert, generates a cancellation PIN, and saves it to the database.
        
        Returns:
            Tuple[int, str]: (alert_id, cancel_pin)
        """
        # Generate a random 4-digit PIN for cancellation security
        pin = ''.join(random.choices(string.digits, k=4))
        
        query = """
            INSERT INTO sos_alerts (user_id, latitude, longitude, message, cancel_pin, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
        """
        params = (user_id, latitude, longitude, message, pin)
        alert_id = self.db.execute_query(query, params)
        
        logger.info(f"SOS Alert {alert_id} triggered for user_id {user_id}. PIN generated.")
        return alert_id, pin

    def cancel_sos(self, user_id: int, pin: str) -> Tuple[bool, str]:
        """
        Cancels an active SOS alert if the provided PIN matches.
        
        Returns:
            Tuple[bool, str]: (success_status, message)
        """
        # Check for an active alert with the matching PIN
        check_query = "SELECT id FROM sos_alerts WHERE user_id = %s AND cancel_pin = %s AND status = 'active'"
        alert = self.db.execute_query(check_query, (user_id, pin), fetch=True)
        
        if not alert:
            logger.warning(f"Failed SOS cancellation attempt for user_id {user_id}: Invalid PIN or no active alert.")
            return False, "Invalid PIN or no active alert found."
        
        # Mark alert as cancelled
        update_query = """
            UPDATE sos_alerts 
            SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """
        self.db.execute_query(update_query, (alert[0]['id'],))
        
        logger.info(f"SOS Alert {alert[0]['id']} cancelled for user_id {user_id}.")
        return True, "SOS alert cancelled successfully."

    def get_unread_count(self, user_id: int) -> int:
        """
        Fetches the total count of unread notifications for a specific user.
        """
        query = "SELECT COUNT(*) as total FROM notifications WHERE user_id = %s AND is_read = FALSE"
        result = self.db.execute_query(query, (user_id,), fetch=True)
        return result[0]['total'] if result else 0