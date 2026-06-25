from app.database import execute_query

class Friend:

    @staticmethod
    def send_request(user_id, friend_id):
        """Send a friend request. Re-opens a previously rejected request."""
        query = """
            INSERT INTO friends (user_id, friend_id, status)
            VALUES (%s, %s, 'pending')
            ON DUPLICATE KEY UPDATE status = 'pending', created_at = CURRENT_TIMESTAMP
        """
        return execute_query(query, (user_id, friend_id))

    @staticmethod
    def accept_request(friendship_id, user_id):
        query = """
            UPDATE friends SET status = 'accepted'
            WHERE id = %s AND friend_id = %s
        """
        return execute_query(query, (friendship_id, user_id))

    @staticmethod
    def reject_request(friendship_id, user_id):
        query = """
            UPDATE friends SET status = 'rejected'
            WHERE id = %s AND friend_id = %s
        """
        return execute_query(query, (friendship_id, user_id))

    @staticmethod
    def remove_friend(user_id, friend_id):
        """Remove an accepted friendship (either direction)."""
        query = """
            DELETE FROM friends
            WHERE ((user_id = %s AND friend_id = %s)
               OR  (user_id = %s AND friend_id = %s))
              AND status = 'accepted'
        """
        return execute_query(query, (user_id, friend_id, friend_id, user_id))

    @staticmethod
    def get_friends(user_id):
        query = """
            SELECT DISTINCT u.id, u.full_name, u.email, u.profile_pic, f.id as friendship_id
            FROM friends f
            JOIN users u ON (
                CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END = u.id
            )
            WHERE (f.user_id = %s OR f.friend_id = %s)
            AND f.status = 'accepted'
        """
        return execute_query(query, (user_id, user_id, user_id), fetch=True)

    @staticmethod
    def get_pending_requests(user_id):
        query = """
            SELECT DISTINCT f.id, f.user_id, f.created_at,
                   u.full_name, u.email, u.profile_pic
            FROM friends f
            JOIN users u ON f.user_id = u.id
            WHERE f.friend_id = %s AND f.status = 'pending'
        """
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def get_sent_requests(user_id):
        query = """
            SELECT DISTINCT f.id, f.friend_id, f.created_at,
                   u.full_name, u.email
            FROM friends f
            JOIN users u ON f.friend_id = u.id
            WHERE f.user_id = %s AND f.status = 'pending'
        """
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def are_friends(user_id, friend_id):
        query = """
            SELECT DISTINCT id FROM friends
            WHERE ((user_id = %s AND friend_id = %s)
               OR  (user_id = %s AND friend_id = %s))
            AND status = 'accepted'
        """
        results = execute_query(query, (user_id, friend_id, friend_id, user_id), fetch=True)
        return bool(results)

    @staticmethod
    def get_friendship_status(user_id, other_id):
        """Return 'accepted', 'pending_sent', 'pending_received', or None."""
        query = """
            SELECT id, user_id, friend_id, status FROM friends
            WHERE (user_id = %s AND friend_id = %s)
               OR (user_id = %s AND friend_id = %s)
            LIMIT 1
        """
        rows = execute_query(query, (user_id, other_id, other_id, user_id), fetch=True)
        if not rows:
            return None, None
        row = rows[0]
        if row['status'] == 'accepted':
            return 'accepted', row['id']
        if row['status'] == 'pending':
            if row['user_id'] == user_id:
                return 'pending_sent', row['id']
            return 'pending_received', row['id']
        return row['status'], row['id']

    @staticmethod
    def search_users(query_str, current_user_id):
        query = """
            SELECT DISTINCT id, full_name, email, profile_pic
            FROM users
            WHERE (full_name LIKE %s OR email LIKE %s)
            AND id != %s
            LIMIT 10
        """
        like = f'%{query_str}%'
        return execute_query(query, (like, like, current_user_id), fetch=True) or []


class AvailabilitySlot:

    @staticmethod
    def create(user_id, date, start_time, end_time, label):
        query = """
            INSERT INTO availability_slots
            (user_id, date, start_time, end_time, label)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (user_id, date, start_time, end_time, label))

    @staticmethod
    def get_by_user(user_id):
        query = """
            SELECT * FROM availability_slots
            WHERE user_id = %s
            ORDER BY date, start_time
        """
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def get_by_user_and_date(user_id, date):
        query = """
            SELECT * FROM availability_slots
            WHERE user_id = %s AND date = %s
            ORDER BY start_time
        """
        return execute_query(query, (user_id, date), fetch=True)

    @staticmethod
    def delete(slot_id, user_id):
        query = "DELETE FROM availability_slots WHERE id = %s AND user_id = %s"
        return execute_query(query, (slot_id, user_id))

    @staticmethod
    def get_common_slots(user_ids):
        """Find common availability across multiple users."""
        if not user_ids:
            return []
        placeholders = ','.join(['%s'] * len(user_ids))
        query = f"""
            SELECT DISTINCT date, start_time, end_time,
                   COUNT(DISTINCT user_id) as available_count
            FROM availability_slots
            WHERE user_id IN ({placeholders})
            GROUP BY date, start_time, end_time
            HAVING available_count = %s
            ORDER BY date, start_time
        """
        return execute_query(query, (*user_ids, len(user_ids)), fetch=True)


class MeetupSchedule:

    @staticmethod
    def create(organizer_id, title, description, proposed_date, proposed_time):
        query = """
            INSERT INTO meetup_schedules
            (organizer_id, title, description, proposed_date, proposed_time)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (organizer_id, title, description,
                                     proposed_date, proposed_time))

    @staticmethod
    def get_by_id(schedule_id):
        query = "SELECT * FROM meetup_schedules WHERE id = %s"
        results = execute_query(query, (schedule_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_user(user_id):
        query = """
            SELECT ms.*, u.full_name as organizer_name
            FROM meetup_schedules ms
            JOIN users u ON ms.organizer_id = u.id
            WHERE ms.organizer_id = %s
               OR ms.id IN (
                   SELECT schedule_id FROM schedule_invites
                   WHERE user_id = %s
               )
            ORDER BY ms.proposed_date, ms.proposed_time
        """
        return execute_query(query, (user_id, user_id), fetch=True)

    @staticmethod
    def confirm(schedule_id, organizer_id):
        query = """
            UPDATE meetup_schedules SET status = 'confirmed'
            WHERE id = %s AND organizer_id = %s
        """
        return execute_query(query, (schedule_id, organizer_id))


class ScheduleInvite:

    @staticmethod
    def create(schedule_id, user_id):
        query = """
            INSERT IGNORE INTO schedule_invites (schedule_id, user_id)
            VALUES (%s, %s)
        """
        return execute_query(query, (schedule_id, user_id))

    @staticmethod
    def respond(invite_id, user_id, status):
        query = """
            UPDATE schedule_invites
            SET status = %s, responded_at = NOW()
            WHERE id = %s AND user_id = %s
        """
        return execute_query(query, (status, invite_id, user_id))

    @staticmethod
    def get_by_schedule(schedule_id):
        query = """
            SELECT si.*, u.full_name, u.email, u.profile_pic
            FROM schedule_invites si
            JOIN users u ON si.user_id = u.id
            WHERE si.schedule_id = %s
        """
        return execute_query(query, (schedule_id,), fetch=True)

    @staticmethod
    def get_pending_by_user(user_id):
        query = """
            SELECT si.*, ms.title, ms.proposed_date,
                   ms.proposed_time, u.full_name as organizer_name
            FROM schedule_invites si
            JOIN meetup_schedules ms ON si.schedule_id = ms.id
            JOIN users u ON ms.organizer_id = u.id
            WHERE si.user_id = %s AND si.status = 'pending'
        """
        return execute_query(query, (user_id,), fetch=True)