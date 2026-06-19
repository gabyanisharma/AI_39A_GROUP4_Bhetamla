from app.database import execute_query


class MeetupGallery:

    @staticmethod
    def get_for_meetup(meetup_id, viewer_id=None):
        rows = execute_query(
            """
            SELECT g.*, u.full_name,
                   (SELECT COUNT(*) FROM gallery_likes gl WHERE gl.gallery_id = g.id) AS like_count,
                   (SELECT COUNT(*) FROM gallery_comments gc WHERE gc.gallery_id = g.id) AS comment_count,
                   EXISTS(
                       SELECT 1 FROM gallery_likes gl2
                       WHERE gl2.gallery_id = g.id AND gl2.user_id = %s
                   ) AS liked_by_me
            FROM meetup_gallery g
            JOIN users u ON u.id = g.user_id
            WHERE g.meetup_id = %s
              AND (g.is_public = TRUE OR g.user_id = %s
                   OR EXISTS (
                       SELECT 1 FROM meetup_members mm
                       WHERE mm.meetup_id = g.meetup_id
                         AND mm.user_id = %s AND mm.status = 'accepted'
                   ))
            ORDER BY g.created_at DESC
            """,
            (viewer_id, meetup_id, viewer_id, viewer_id), fetch=True
        )
        return rows or []

    @staticmethod
    def add(meetup_id, user_id, file_path, caption='', is_public=True):
        return execute_query(
            """
            INSERT INTO meetup_gallery
            (meetup_id, user_id, file_path, caption, is_public)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (meetup_id, user_id, file_path, caption, is_public)
        )

    @staticmethod
    def get_by_id(photo_id):
        rows = execute_query(
            "SELECT * FROM meetup_gallery WHERE id = %s",
            (photo_id,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def delete(photo_id, user_id):
        execute_query(
            "DELETE FROM meetup_gallery WHERE id = %s AND user_id = %s",
            (photo_id, user_id)
        )

    @staticmethod
    def set_privacy(photo_id, user_id, is_public):
        execute_query(
            """
            UPDATE meetup_gallery SET is_public = %s
            WHERE id = %s AND user_id = %s
            """,
            (is_public, photo_id, user_id)
        )

    @staticmethod
    def toggle_like(photo_id, user_id):
        existing = execute_query(
            """
            SELECT id FROM gallery_likes
            WHERE gallery_id = %s AND user_id = %s
            """,
            (photo_id, user_id), fetch=True
        )
        if existing:
            execute_query(
                "DELETE FROM gallery_likes WHERE gallery_id = %s AND user_id = %s",
                (photo_id, user_id)
            )
            return False
        execute_query(
            "INSERT INTO gallery_likes (gallery_id, user_id) VALUES (%s, %s)",
            (photo_id, user_id)
        )
        return True

    @staticmethod
    def add_comment(photo_id, user_id, comment):
        return execute_query(
            """
            INSERT INTO gallery_comments (gallery_id, user_id, comment)
            VALUES (%s, %s, %s)
            """,
            (photo_id, user_id, comment)
        )

    @staticmethod
    def get_comments(photo_id):
        return execute_query(
            """
            SELECT gc.*, u.full_name
            FROM gallery_comments gc
            JOIN users u ON u.id = gc.user_id
            WHERE gc.gallery_id = %s
            ORDER BY gc.created_at ASC
            """,
            (photo_id,), fetch=True
        ) or []
