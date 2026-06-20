from app.database import execute_query

class EmergencyContact:

    @staticmethod
    def create(user_id, name, phone, relationship, email=None):
        query = """
            INSERT INTO emergency_contacts (user_id, name, phone, relationship, email)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (user_id, name, phone, relationship, email or None))

    @staticmethod
    def get_by_user(user_id):
        query = "SELECT * FROM emergency_contacts WHERE user_id = %s"
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def delete(contact_id, user_id):
        query = "DELETE FROM emergency_contacts WHERE id = %s AND user_id = %s"
        return execute_query(query, (contact_id, user_id))

    @staticmethod
    def get_by_id(contact_id):
        query = "SELECT * FROM emergency_contacts WHERE id = %s"
        results = execute_query(query, (contact_id,), fetch=True)
        return results[0] if results else None


class SOSAlert:

    @staticmethod
    def create(user_id, latitude, longitude, message, cancel_pin):
        query = """
            INSERT INTO sos_alerts
            (user_id, latitude, longitude, message, cancel_pin)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (user_id, latitude, longitude, message, cancel_pin))

    @staticmethod
    def get_active(user_id):
        query = """
            SELECT * FROM sos_alerts
            WHERE user_id = %s AND status = 'active'
            ORDER BY triggered_at DESC LIMIT 1
        """
        results = execute_query(query, (user_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def cancel(alert_id, user_id):
        query = """
            UPDATE sos_alerts
            SET status = 'cancelled', cancelled_at = NOW()
            WHERE id = %s AND user_id = %s
        """
        return execute_query(query, (alert_id, user_id))

    @staticmethod
    def get_all_by_user(user_id):
        query = """
            SELECT * FROM sos_alerts
            WHERE user_id = %s
            ORDER BY triggered_at DESC
        """
        return execute_query(query, (user_id,), fetch=True)


class Notification:

    @staticmethod
    def create(user_id, title, message, type='general', link=None):
        query = """
            INSERT INTO notifications
            (user_id, title, message, type, link)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (user_id, title, message, type, link))

    @staticmethod
    def get_by_user(user_id, limit=20):
        query = """
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch=True)

    @staticmethod
    def get_unread_count(user_id):
        query = """
            SELECT COUNT(*) as count FROM notifications
            WHERE user_id = %s AND is_read = FALSE
        """
        results = execute_query(query, (user_id,), fetch=True)
        return results[0]['count'] if results else 0

    @staticmethod
    def mark_read(notification_id, user_id):
        query = """
            UPDATE notifications SET is_read = TRUE
            WHERE id = %s AND user_id = %s
        """
        return execute_query(query, (notification_id, user_id))

    @staticmethod
    def mark_all_read(user_id):
        query = """
            UPDATE notifications SET is_read = TRUE
            WHERE user_id = %s
        """
        return execute_query(query, (user_id,))

    @staticmethod
    def delete(notification_id, user_id):
        query = """
            DELETE FROM notifications
            WHERE id = %s AND user_id = %s
        """
        return execute_query(query, (notification_id, user_id))

    @staticmethod
    def delete_all(user_id):
        query = "DELETE FROM notifications WHERE user_id = %s"
        return execute_query(query, (user_id,))