import logging
from typing import Optional, Dict, Any, List
from app.database_manager import DatabaseManager

logger = logging.getLogger('user_service')

class UserService:
    def __init__(self):
        self.db = DatabaseManager()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves basic user information by their ID."""
        query = "SELECT id, full_name, email, created_at FROM users WHERE id = %s"
        result = self.db.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    def get_user_friends(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Fetches the list of accepted friends for a user.
        This is used by the meetup planner to populate the invite list.
        """
        query = """
            SELECT u.id, u.full_name, u.email 
            FROM users u
            JOIN friendships f ON (u.id = f.friend_id OR u.id = f.user_id)
            WHERE (f.user_id = %s OR f.friend_id = %s)
            AND u.id != %s
            AND f.status = 'accepted'
        """
        results = self.db.execute_query(query, (user_id, user_id, user_id), fetch=True)
        return results if results else []

    def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """
        Aggregates statistical data for the user dashboard.
        """
        stats = {
            'meetups_count': 0,
            'friends_count': 0,
            'pending_requests': 0
        }
        
        # Count user-created meetups
        m_res = self.db.execute_query("SELECT COUNT(*) as total FROM meetups WHERE creator_id = %s", (user_id,), fetch=True)
        if m_res: stats['meetups_count'] = m_res[0]['total']
        
        # Count accepted friends
        f_res = self.db.execute_query(
            "SELECT COUNT(*) as total FROM friendships WHERE (user_id = %s OR friend_id = %s) AND status = 'accepted'",
            (user_id, user_id), fetch=True
        )
        if f_res: stats['friends_count'] = f_res[0]['total']
        
        logger.info(f"Dashboard data retrieved for user_id: {user_id}")
        return stats