from datetime import datetime, timedelta

from app.database import execute_query


class GroupVote:

    @staticmethod
    def get_active_for_meetup(meetup_id):
        rows = execute_query(
            """
            SELECT * FROM venue_votes
            WHERE meetup_id = %s AND status = 'open'
            ORDER BY created_at DESC LIMIT 1
            """,
            (meetup_id,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_by_id(vote_id):
        rows = execute_query(
            "SELECT * FROM venue_votes WHERE id = %s",
            (vote_id,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def create(meetup_id, created_by, option_specs, hours=24):
        """option_specs: list of dicts with restaurant_id, label, address."""
        deadline = datetime.now() + timedelta(hours=hours)
        vote_id = execute_query(
            """
            INSERT INTO venue_votes (meetup_id, created_by, deadline, status)
            VALUES (%s, %s, %s, 'open')
            """,
            (meetup_id, created_by, deadline)
        )
        for opt in option_specs[:3]:
            execute_query(
                """
                INSERT INTO venue_vote_options (vote_id, restaurant_id, label, address)
                VALUES (%s, %s, %s, %s)
                """,
                (vote_id, opt.get('restaurant_id'), opt['label'], opt.get('address'))
            )
        return vote_id

    @staticmethod
    def get_options(vote_id):
        return execute_query(
            "SELECT * FROM venue_vote_options WHERE vote_id = %s ORDER BY id",
            (vote_id,), fetch=True
        ) or []

    @staticmethod
    def cast_vote(vote_id, user_id, option_id):
        execute_query(
            """
            INSERT INTO venue_vote_casts (vote_id, option_id, user_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE option_id = VALUES(option_id)
            """,
            (vote_id, option_id, user_id)
        )

    @staticmethod
    def get_user_cast(vote_id, user_id):
        rows = execute_query(
            """
            SELECT option_id FROM venue_vote_casts
            WHERE vote_id = %s AND user_id = %s
            """,
            (vote_id, user_id), fetch=True
        )
        return rows[0]['option_id'] if rows else None

    @staticmethod
    def get_results(vote_id):
        return execute_query(
            """
            SELECT o.id, o.label, o.address, o.restaurant_id,
                   COUNT(c.id) AS vote_count
            FROM venue_vote_options o
            LEFT JOIN venue_vote_casts c ON c.option_id = o.id
            WHERE o.vote_id = %s
            GROUP BY o.id, o.label, o.address, o.restaurant_id
            ORDER BY vote_count DESC, o.id
            """,
            (vote_id,), fetch=True
        ) or []

    @staticmethod
    def close_expired():
        """Close all open votes past deadline. Returns list of closed vote ids."""
        expired = execute_query(
            """
            SELECT id, meetup_id FROM venue_votes
            WHERE status = 'open' AND deadline <= NOW()
            """,
            fetch=True
        ) or []
        closed_ids = []
        for vote in expired:
            GroupVote._finalize_vote(vote['id'], vote['meetup_id'])
            closed_ids.append(vote['id'])
        return closed_ids

    @staticmethod
    def _finalize_vote(vote_id, meetup_id):
        results = GroupVote.get_results(vote_id)
        if not results:
            execute_query(
                "UPDATE venue_votes SET status = 'closed' WHERE id = %s",
                (vote_id,)
            )
            return None

        # Draw / tie detection: if top two options share the same vote count,
        # mark as 'draw' instead of picking an arbitrary winner.
        if len(results) >= 2 and results[0]['vote_count'] == results[1]['vote_count']:
            execute_query(
                "UPDATE venue_votes SET status = 'draw' WHERE id = %s",
                (vote_id,)
            )
            return {'is_tie': True, 'tied_options': results}

        winner = results[0]
        execute_query(
            """
            UPDATE venue_votes
            SET status = 'closed', winner_option_id = %s
            WHERE id = %s
            """,
            (winner['id'], vote_id)
        )
        execute_query(
            """
            UPDATE meetups
            SET winning_restaurant_id = %s,
                winning_venue_name = %s,
                midpoint_address = COALESCE(%s, midpoint_address)
            WHERE id = %s
            """,
            (winner.get('restaurant_id'), winner['label'],
             winner.get('address'), meetup_id)
        )
        return winner
