"""
models/fare_alert_model.py
Bhetamल — Fare Drop Alert Feature
----------------------------------
Pure data-access layer. No Flask, no HTTP, no session.
All functions accept explicit arguments and return plain dicts / lists.
"""

import random
import os
from datetime import datetime
from config import Config
from app.database import get_db_connection

FARE_MODES = ('car', 'bike', 'public', 'walk')
RATE_PER_KM = {
    'car': 35,
    'bike': 18,
    'public': 5,
    'walk': 0,
}

# ── DB connection ─────────────────────────────────────────────────────────────
def get_db():
    return get_db_connection()


def estimate_fare(distance_km: float, mode: str) -> float:
    """Return estimated fare in NPR for a given distance + travel mode."""
    if mode == 'bike':
        base = 25 + 18 * distance_km
    elif mode == 'car':
        base = 50 + 35 * distance_km
    elif mode == 'taxi':
        base = 50 + 45 * distance_km
    elif mode == 'public':
        base = 25 + 5 * distance_km
    elif mode == 'walk':
        base = 0.0
    else:
        base = 0.0
        
    fluctuation = random.uniform(0.85, 1.15)   # ← simulate peak/off-peak fluctuation
    return round(base * fluctuation, 2)


# ── Distance helper ───────────────────────────────────────────────────────────
def get_distance(meetup_id: int, user_id: int) -> float:
    """
    Return stored travel distance (km) from travel_estimate.
    Falls back to a realistic Kathmandu city mock (3–18 km).
    """
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT distance FROM travel_estimate
            WHERE  meetupID = %s AND userID = %s
            ORDER BY createdAt DESC
            LIMIT 1
        """, (meetup_id, user_id))
        row = cur.fetchone()
        if row and row['distance']:
            return float(row['distance'])
    finally:
        cur.close()
        db.close()
    return round(random.uniform(3.0, 18.0), 2)


# ── Alert queries ─────────────────────────────────────────────────────────────
def get_alerts_for_user(user_id: int) -> list[dict]:
    """Return all active fare-drop alerts for a user."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT fa.*,
                   m.title          AS meetup_title,
                   STR_TO_DATE(CONCAT(m.meetup_date, ' ', m.meetup_time), '%%Y-%%m-%%d %%H:%%i:%%s') AS meetupDateTime,
                   m.midpoint_address AS destination
            FROM   fare_alert fa
            JOIN   meetups      m  ON m.id        = fa.meetupID
            WHERE  fa.userID   = %s
              AND  fa.isActive = 1
            ORDER BY fa.createdAt DESC
        """, (user_id,))
        return cur.fetchall()
    finally:
        cur.close()
        db.close()


def get_alert_for_meetup(user_id: int, meetup_id: int) -> dict | None:
    """Return the active alert for a specific user + meetup combo (if any)."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT * FROM fare_alert
            WHERE  userID   = %s
              AND  meetupID = %s
              AND  isActive = 1
            LIMIT 1
        """, (user_id, meetup_id))
        return cur.fetchone()
    finally:
        cur.close()
        db.close()


def create_alert(user_id: int, meetup_id: int, mode: str,
                 target_fare: float, current_fare: float) -> int:
    """
    Deactivate any existing alert for the same user/meetup/mode,
    then insert a new one. Returns the new alertID.
    """
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE fare_alert
            SET    isActive = 0
            WHERE  userID = %s AND meetupID = %s AND mode = %s
        """, (user_id, meetup_id, mode))

        cur.execute("""
            INSERT INTO fare_alert (userID, meetupID, mode, targetFare, currentFare)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, meetup_id, mode, target_fare, current_fare))

        db.commit()
        return cur.lastrowid
    finally:
        cur.close()
        db.close()


def deactivate_alert(alert_id: int, user_id: int) -> bool:
    """Soft-delete an alert. Returns True if a row was updated."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE fare_alert
            SET    isActive = 0
            WHERE  alertID = %s AND userID = %s
        """, (alert_id, user_id))
        db.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        db.close()


def get_pending_alert_targets() -> list[dict]:
    """All active, not-yet-triggered (user, meetup, mode) combos across every
    user. Used by the background scheduler to auto-check fare drops."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT userID, meetupID, mode
            FROM   fare_alert
            WHERE  isActive = 1 AND isTriggered = 0
        """)
        return cur.fetchall()
    finally:
        cur.close()
        db.close()


# ── Meetup queries ────────────────────────────────────────────────────────────
def get_meetup(meetup_id: int) -> dict | None:
    """Return meetup row with destination address and coordinates."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT m.*, m.midpoint_address AS destination, m.midpoint_lat AS latitude, m.midpoint_lng AS longitude,
                   STR_TO_DATE(CONCAT(m.meetup_date, ' ', m.meetup_time), '%%Y-%%m-%%d %%H:%%i:%%s') AS meetupDateTime
            FROM   meetups m
            WHERE  m.id = %s
        """, (meetup_id,))
        return cur.fetchone()
    finally:
        cur.close()
        db.close()


# ── Fare history ──────────────────────────────────────────────────────────────
def get_fare_history(meetup_id: int, limit: int = 60) -> list[dict]:
    """Return recent fare readings for all modes (used by sparkline)."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT mode, fare, recordedAt
            FROM   fare_history
            WHERE  meetupID = %s
            ORDER BY recordedAt ASC
            LIMIT %s
        """, (meetup_id, limit))
        return cur.fetchall()
    finally:
        cur.close()
        db.close()


def record_fare_history(meetup_id: int, mode: str, fare: float) -> None:
    """Persist one fare reading to fare_history."""
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO fare_history (meetupID, mode, fare)
            VALUES (%s, %s, %s)
        """, (meetup_id, mode, fare))
        db.commit()
    finally:
        cur.close()
        db.close()


# ── Alert triggering ──────────────────────────────────────────────────────────
def check_and_trigger_alerts(meetup_id: int, mode: str, fare: float) -> list[dict]:
    """
    Find active, untriggered alerts where targetFare >= current fare,
    mark them triggered, and return the list so the controller can
    build notifications.
    """
    db  = get_db()
    cur = db.cursor()
    triggered = []
    try:
        cur.execute("""
            SELECT * FROM fare_alert
            WHERE  meetupID    = %s
              AND  mode        = %s
              AND  isActive    = 1
              AND  isTriggered = 0
              AND  targetFare >= %s
        """, (meetup_id, mode, fare))

        for alert in cur.fetchall():
            cur.execute("""
                UPDATE fare_alert
                SET    isTriggered = 1,
                       triggeredAt = NOW(),
                       currentFare = %s
                WHERE  alertID = %s
            """, (fare, alert['alertID']))
            triggered.append({
                'alertID':    alert['alertID'],
                'userID':     alert['userID'],
                'mode':       mode,
                'fare':       fare,
                'targetFare': float(alert['targetFare']),
                'saving':     round(float(alert['targetFare']) - fare, 2),
            })
        db.commit()
    finally:
        cur.close()
        db.close()
    return triggered


# ── History grouping utility ──────────────────────────────────────────────────
def group_history_by_mode(rows: list[dict]) -> dict:
    """
    Transform raw fare_history rows into
    { mode: [{fare, time}, ...], ... }
    """
    grouped = {m: [] for m in FARE_MODES}
    for row in rows:
        grouped.setdefault(row['mode'], []).append({
            'fare': float(row['fare']),
            'time': row['recordedAt'].strftime('%H:%M'),
        })
    return grouped
