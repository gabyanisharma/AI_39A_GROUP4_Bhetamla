from app.database import execute_query


class FriendGroup:

    GLOBAL_GROUP_NAME = 'Bhetamla Community Chat'

    @staticmethod
    def ensure_global_room():
        """Get or create the single app-wide chat room every user shares."""
        rows = execute_query(
            """
            SELECT id FROM friend_groups
            WHERE name = %s
            ORDER BY id LIMIT 1
            """,
            (FriendGroup.GLOBAL_GROUP_NAME,), fetch=True
        )
        if rows:
            group_id = rows[0]['id']
            # Ensure existing group is marked as a chat group
            execute_query(
                "UPDATE friend_groups SET is_chat_group = TRUE WHERE id = %s",
                (group_id,)
            )
            return group_id

        # owner_id is NOT NULL with ON DELETE CASCADE in the schema, so we
        # anchor the room to the earliest-registered account rather than
        # leaving it NULL or tying it to whichever user happens to trigger
        # creation first. Ownership has no special meaning for this room —
        # FriendGroup.is_member() is what actually gates access.
        anchor = execute_query(
            "SELECT id FROM users ORDER BY id LIMIT 1",
            fetch=True
        )
        anchor_id = anchor[0]['id'] if anchor else None
        if anchor_id is None:
            return None

        return execute_query(
            """
            INSERT INTO friend_groups (name, owner_id, is_chat_group)
            VALUES (%s, %s, TRUE)
            """,
            (FriendGroup.GLOBAL_GROUP_NAME, anchor_id)
        )

    @staticmethod
    def ensure_member(user_id):
        """Make sure this user is in the global room, then return its id."""
        group_id = FriendGroup.ensure_global_room()
        execute_query(
            """
            INSERT IGNORE INTO friend_group_members (group_id, user_id)
            VALUES (%s, %s)
            """,
            (group_id, user_id)
        )
        return group_id

    @staticmethod
    def get_for_user(user_id):
        """Every user is in exactly one room: the global one."""
        group_id = FriendGroup.ensure_member(user_id)
        rows = execute_query(
            "SELECT * FROM friend_groups WHERE id = %s",
            (group_id,), fetch=True
        )
        return rows or []

    @staticmethod
    def is_member(group_id, user_id):
        rows = execute_query(
            """
            SELECT id FROM friend_group_members
            WHERE group_id = %s AND user_id = %s
            """,
            (group_id, user_id), fetch=True
        )
        return bool(rows)

    @staticmethod
    def get_members(group_id):
        return execute_query(
            """
            SELECT u.id, u.full_name, u.profile_pic
            FROM friend_group_members fgm
            JOIN users u ON u.id = fgm.user_id
            WHERE fgm.group_id = %s
            ORDER BY u.full_name
            """,
            (group_id,), fetch=True
        ) or []


class GroupChat:

    @staticmethod
    def post_message(group_id, user_id, body):
        return execute_query(
            """
            INSERT INTO group_chat_messages (group_id, user_id, body)
            VALUES (%s, %s, %s)
            """,
            (group_id, user_id, body.strip())
        )

    @staticmethod
    def get_messages(group_id, limit=100):
        return execute_query(
            """
            SELECT m.*, u.full_name, u.profile_pic,
                   (SELECT COUNT(*) FROM group_chat_reads r WHERE r.message_id = m.id) AS read_count
            FROM group_chat_messages m
            JOIN users u ON u.id = m.user_id
            WHERE m.group_id = %s AND m.is_deleted = FALSE
            ORDER BY m.created_at ASC
            LIMIT %s
            """,
            (group_id, limit), fetch=True
        ) or []

    @staticmethod
    def get_message(message_id):
        rows = execute_query(
            """
            SELECT m.*, u.full_name, u.profile_pic
            FROM group_chat_messages m
            JOIN users u ON u.id = m.user_id
            WHERE m.id = %s
            """,
            (message_id,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def soft_delete(message_id, user_id):
        execute_query(
            """
            UPDATE group_chat_messages
            SET is_deleted = TRUE, body = '[deleted]'
            WHERE id = %s AND user_id = %s
            """,
            (message_id, user_id)
        )

    @staticmethod
    def mark_read(message_id, user_id):
        execute_query(
            """
            INSERT IGNORE INTO group_chat_reads (message_id, user_id)
            VALUES (%s, %s)
            """,
            (message_id, user_id)
        )

    @staticmethod
    def mark_all_read(group_id, user_id):
        execute_query(
            """
            INSERT IGNORE INTO group_chat_reads (message_id, user_id)
            SELECT m.id, %s FROM group_chat_messages m
            WHERE m.group_id = %s AND m.user_id != %s AND m.is_deleted = FALSE
            """,
            (user_id, group_id, user_id)
        )

    @staticmethod
    def set_typing(group_id, user_id):
        execute_query(
            """
            INSERT INTO group_chat_typing (group_id, user_id, updated_at)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE updated_at = NOW()
            """,
            (group_id, user_id)
        )

    @staticmethod
    def get_typing_users(group_id, exclude_user_id):
        return execute_query(
            """
            SELECT u.full_name FROM group_chat_typing t
            JOIN users u ON u.id = t.user_id
            WHERE t.group_id = %s AND t.user_id != %s
              AND t.updated_at >= DATE_SUB(NOW(), INTERVAL 5 SECOND)
            """,
            (group_id, exclude_user_id), fetch=True
        ) or []

    @staticmethod
    def get_read_receipts(message_id):
        return execute_query(
            """
            SELECT u.full_name, r.read_at
            FROM group_chat_reads r
            JOIN users u ON u.id = r.user_id
            WHERE r.message_id = %s
            ORDER BY r.read_at ASC
            """,
            (message_id,), fetch=True
        ) or []