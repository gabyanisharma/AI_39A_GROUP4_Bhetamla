from app.database import execute_query
from app.models.achievement import Achievement
from app.controllers.notification_controller import send_notification


def unlock_achievement(user_id, unlock_key):
    """Unlock badge and notify user. Returns achievement dict if newly unlocked."""
    if Achievement.has_unlocked(user_id, unlock_key):
        return None
    ach = Achievement.get_by_key(unlock_key)
    if not ach:
        return None
    Achievement.unlock(user_id, unlock_key)
    send_notification(
        user_id,
        f"Achievement Unlocked: {ach['title']}",
        ach['description'],
        type='achievement',
        link='/meetup/groups'
    )
    return ach


def check_first_contact(user_id):
    rows = execute_query(
        """
        SELECT COUNT(DISTINCT m.id) AS cnt
        FROM meetups m
        LEFT JOIN meetup_members mm
          ON mm.meetup_id = m.id AND mm.user_id = %s
        WHERE m.created_by = %s
           OR (mm.status = 'accepted')
        """,
        (user_id, user_id), fetch=True
    )
    if rows and rows[0]['cnt'] >= 1:
        unlock_achievement(user_id, 'first_contact')


def check_road_tripper(user_id):
    rows = execute_query(
        """
        SELECT COUNT(*) AS cnt FROM meetup_members mm
        JOIN meetups m ON m.id = mm.meetup_id
        WHERE mm.user_id = %s AND mm.status = 'accepted'
          AND m.status = 'completed'
        """,
        (user_id,), fetch=True
    )
    if rows and rows[0]['cnt'] >= 5:
        unlock_achievement(user_id, 'road_tripper')


def check_lifeline(user_id):
    contacts = execute_query(
        "SELECT COUNT(*) AS cnt FROM emergency_contacts WHERE user_id = %s",
        (user_id,), fetch=True
    )
    if contacts and contacts[0]['cnt'] >= 1:
        unlock_achievement(user_id, 'lifeline')


def check_reliable_rider(user_id):
    rows = execute_query(
        """
        SELECT m.meetup_date FROM meetup_members mm
        JOIN meetups m ON m.id = mm.meetup_id
        WHERE mm.user_id = %s AND mm.status = 'accepted'
          AND m.status = 'completed' AND m.meetup_date IS NOT NULL
        ORDER BY m.meetup_date DESC
        LIMIT 10
        """,
        (user_id,), fetch=True
    ) or []
    if len(rows) < 3:
        return
    streak = 1
    for i in range(1, len(rows)):
        prev = rows[i - 1]['meetup_date']
        curr = rows[i]['meetup_date']
        if prev and curr and (prev - curr).days == 1:
            streak += 1
            if streak >= 3:
                unlock_achievement(user_id, 'reliable_rider')
                return
        else:
            streak = 1


def on_meetup_joined(user_id):
    check_first_contact(user_id)


def on_meetup_created(user_id):
    check_first_contact(user_id)


def on_meetup_completed(user_id):
    check_road_tripper(user_id)
    check_reliable_rider(user_id)


def on_budget_split_used(user_id):
    unlock_achievement(user_id, 'penny_pincher')


def on_vote_created(user_id):
    unlock_achievement(user_id, 'democratic_leader')


def on_chat_message(user_id):
    unlock_achievement(user_id, 'social_butterfly')


def on_emergency_contact_added(user_id):
    check_lifeline(user_id)
