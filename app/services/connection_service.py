"""F19 — Pairwise connection badges.

Badges are earned from the frequency of interaction *between two users*
(shared meetups + group-chat messages). Interaction counts are tracked per
unordered user pair in the `user_bonds` table, a badge level unlocks when a
combined-interaction threshold is reached, and the bond is visible in both
users' profiles (the table is symmetric, queried from either side).
"""

from app.database import execute_query
from app.controllers.notification_controller import send_notification


# (threshold on meetup_count + chat_count, level, label)
BOND_TIERS = [
    (3,  1, 'Acquaintances'),
    (10, 2, 'Companions'),
    (25, 3, 'Inseparable'),
]


def _pair(a, b):
    """Return the canonical (low, high) ordering, or None for a self-pair."""
    a, b = int(a), int(b)
    if a == b:
        return None
    return (a, b) if a < b else (b, a)


def _level_for(total):
    level, label = 0, None
    for threshold, lvl, lbl in BOND_TIERS:
        if total >= threshold:
            level, label = lvl, lbl
    return level, label


def _bump(user_a, user_b, *, meetup=0, chat=0):
    """Increment a single pair's counters and unlock a badge tier if crossed."""
    pair = _pair(user_a, user_b)
    if not pair:
        return
    low, high = pair

    execute_query(
        """
        INSERT INTO user_bonds (user_low, user_high, meetup_count, chat_count)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            meetup_count = meetup_count + VALUES(meetup_count),
            chat_count   = chat_count   + VALUES(chat_count)
        """,
        (low, high, meetup, chat),
    )

    rows = execute_query(
        "SELECT meetup_count, chat_count, badge_level FROM user_bonds "
        "WHERE user_low = %s AND user_high = %s",
        (low, high), fetch=True,
    )
    if not rows:
        return
    row = rows[0]
    total = (row['meetup_count'] or 0) + (row['chat_count'] or 0)
    new_level, label = _level_for(total)

    if new_level > (row['badge_level'] or 0):
        execute_query(
            "UPDATE user_bonds SET badge_level = %s "
            "WHERE user_low = %s AND user_high = %s",
            (new_level, low, high),
        )
        _notify_bond(low, high, label)


def _user_name(user_id):
    rows = execute_query("SELECT full_name FROM users WHERE id = %s",
                         (user_id,), fetch=True)
    return rows[0]['full_name'] if rows else 'a friend'


def _notify_bond(low, high, label):
    low_name, high_name = _user_name(low), _user_name(high)
    send_notification(
        low, f'New Bond Badge: {label}',
        f'You and {high_name} reached the “{label}” connection badge!',
        type='achievement', link='/user/profile',
    )
    send_notification(
        high, f'New Bond Badge: {label}',
        f'You and {low_name} reached the “{label}” connection badge!',
        type='achievement', link='/user/profile',
    )


# ── Public hooks ───────────────────────────────────────────────────────────

def record_meetup_bond(user_id, other_user_ids):
    """Count a shared meetup between user_id and each other accepted member."""
    for other in other_user_ids or []:
        _bump(user_id, other, meetup=1)


def record_chat_bond(user_id, other_user_ids):
    """Count a chat interaction between the sender and each other member."""
    for other in other_user_ids or []:
        _bump(user_id, other, chat=1)


def get_bonds_for_user(user_id):
    """Return this user's bonds (with the other person + badge) for the profile.

    Works from either side of the pair, so both users see the same bond.
    """
    user_id = int(user_id)
    rows = execute_query(
        """
        SELECT
            CASE WHEN user_low = %s THEN user_high ELSE user_low END AS other_id,
            meetup_count, chat_count, badge_level
        FROM user_bonds
        WHERE (user_low = %s OR user_high = %s) AND badge_level > 0
        ORDER BY badge_level DESC, (meetup_count + chat_count) DESC
        """,
        (user_id, user_id, user_id), fetch=True,
    ) or []

    label_by_level = {lvl: lbl for _, lvl, lbl in BOND_TIERS}
    bonds = []
    for r in rows:
        bonds.append({
            'other_id': r['other_id'],
            'other_name': _user_name(r['other_id']),
            'meetup_count': r['meetup_count'] or 0,
            'chat_count': r['chat_count'] or 0,
            'badge_level': r['badge_level'] or 0,
            'badge_label': label_by_level.get(r['badge_level'], ''),
        })
    return bonds
