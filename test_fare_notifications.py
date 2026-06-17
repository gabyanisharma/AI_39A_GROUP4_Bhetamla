#!/usr/bin/env python3
"""
test_fare_notifications.py
Bhetamल — Fare Drop Alert Notification Test Script
────────────────────────────────────────────────────
Run this script while the Flask app is NOT running (it uses the DB directly).
It will:
  1. Ensure the DB schema is up to date
  2. Create a test meetup if none exists
  3. Create a fare alert for user 1
  4. Simulate a fare drop that triggers the alert
  5. Send a notification (visible in the UI notification bell)
  6. Print a summary of all notifications for the user

Usage:
    python test_fare_notifications.py
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.database import get_db_connection, execute_query
from app.models.notification import Notification
from app.controllers.notification_controller import (
    send_notification,
    fare_drop_notification,
)
from app.models.fare_alert_model import (
    create_alert,
    check_and_trigger_alerts,
    record_fare_history,
    estimate_fare,
    get_distance,
    get_alerts_for_user,
    deactivate_alert,
)

# ── Colour helpers for terminal output ─────────────────────────────────────
GREEN  = '\033[92m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
RED    = '\033[91m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def header(text):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")

def step(num, text):
    print(f"\n{BOLD}{YELLOW}  [{num}] {text}{RESET}")

def ok(text):
    print(f"      {GREEN}✓ {text}{RESET}")

def fail(text):
    print(f"      {RED}✗ {text}{RESET}")

def info(text):
    print(f"      {CYAN}ℹ {text}{RESET}")


# ── Main test ──────────────────────────────────────────────────────────────
def main():
    header("Fare Drop Alert — Notification Test")

    # Create the Flask app so DB is initialised
    app = create_app()

    with app.app_context():
        # ──────────────────────────────────────────────────────────────
        step(1, "Verify all users exist")
        # ──────────────────────────────────────────────────────────────
        users = execute_query(
            "SELECT id, full_name, email FROM users",
            fetch=True
        )
        if not users:
            fail("No users found in database. Run the app once to seed demo data.")
            sys.exit(1)
        ok(f"Found {len(users)} user(s):")
        for u in users:
            info(f"  - User ID {u['id']}: {u['full_name']} ({u['email']})")

        # ──────────────────────────────────────────────────────────────
        step(2, "Create (or reuse) a test meetup & add all users as members")
        # ──────────────────────────────────────────────────────────────
        meetup_row = execute_query(
            "SELECT id, title FROM meetups ORDER BY id DESC LIMIT 1",
            fetch=True
        )
        if meetup_row:
            meetup_id    = meetup_row[0]['id']
            meetup_title = meetup_row[0]['title']
            ok(f"Reusing meetup #{meetup_id}: «{meetup_title}»")
        else:
            meetup_id = execute_query(
                """INSERT INTO meetups (title, description, created_by,
                   midpoint_lat, midpoint_lng, midpoint_address,
                   meetup_date, meetup_time)
                   VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), '14:00:00')""",
                (
                    'Test Meetup — Fare Alert Demo',
                    'Auto-created for notification testing',
                    users[0]['id'],
                    27.7172, 85.3240,
                    'Thamel, Kathmandu',
                )
            )
            meetup_title = 'Test Meetup — Fare Alert Demo'
            ok(f"Created new meetup #{meetup_id}: «{meetup_title}»")

        # Ensure ALL users are accepted members of this meetup
        for u in users:
            execute_query(
                """INSERT IGNORE INTO meetup_members (meetup_id, user_id, status)
                   VALUES (%s, %s, 'accepted')""",
                (meetup_id, u['id'])
            )
            ok(f"Ensured user {u['full_name']} is a member of meetup #{meetup_id}")

        # ──────────────────────────────────────────────────────────────
        step(3, "Send a simple test notification to all users")
        # ──────────────────────────────────────────────────────────────
        for u in users:
            notif_id = send_notification(
                user_id=u['id'],
                title="🧪 Test Notification",
                message=f"This is a test notification for {u['full_name']} from the fare alert test script. If you see this in the UI, notifications are working!",
                type='general',
                link=f'/fare-alert/meetup/{meetup_id}'
            )
            ok(f"Notification #{notif_id} created for {u['full_name']}")

        # ──────────────────────────────────────────────────────────────
        step(4, "Create a fare alert (target NPR 150 for Car) for all users")
        # ──────────────────────────────────────────────────────────────
        current_fare = 200.0  # Simulated current fare
        target_fare  = 150.0  # Our target

        for u in users:
            # Deactivate any existing alerts for clean testing
            existing = get_alerts_for_user(u['id'])
            for a in existing:
                deactivate_alert(a['alertID'], u['id'])
            info(f"Deactivated {len(existing)} existing alert(s) for user {u['full_name']}")

            alert_id = create_alert(
                user_id=u['id'],
                meetup_id=meetup_id,
                mode='car',
                target_fare=target_fare,
                current_fare=current_fare,
            )
            ok(f"Alert #{alert_id} created for {u['full_name']}: target=NPR {target_fare}, current=NPR {current_fare}")

        # ──────────────────────────────────────────────────────────────
        step(5, "Simulate fare drop + trigger alert")
        # ──────────────────────────────────────────────────────────────
        dropped_fare = 138.50  # Below target → triggers!
        info(f"Simulating fare drop: NPR {current_fare} → NPR {dropped_fare}")

        # Record the fare history
        record_fare_history(meetup_id, 'car', current_fare)
        record_fare_history(meetup_id, 'car', 185.0)
        record_fare_history(meetup_id, 'car', 170.0)
        record_fare_history(meetup_id, 'car', dropped_fare)
        ok("Fare history recorded (4 data points)")

        # Check and trigger alerts
        triggered = check_and_trigger_alerts(meetup_id, 'car', dropped_fare)

        if triggered:
            ok(f"{len(triggered)} alert(s) triggered!")
            for t in triggered:
                info(f"  Alert #{t['alertID']} (User #{t['userID']}): fare=NPR {t['fare']}, saving=NPR {t['saving']}")
        else:
            fail("No alerts triggered — alerts may have been already triggered or conditions not met")

        # ──────────────────────────────────────────────────────────────
        step(6, "Send fare-drop notifications (rich format) to all triggered users")
        # ──────────────────────────────────────────────────────────────
        saving = round(target_fare - dropped_fare, 2)
        for t in triggered:
            notif_id = fare_drop_notification(
                user_id=t['userID'],
                mode='car',
                fare=dropped_fare,
                target_fare=target_fare,
                saving=saving,
                meetup_id=meetup_id,
                meetup_title=meetup_title,
            )
            ok(f"Rich fare-drop notification #{notif_id} created for User #{t['userID']}")

        # Also send extra demo notifications for other modes to all users as demonstration
        for u in users:
            for mode, fare in [('bike', 95.0), ('public', 42.0)]:
                nid = fare_drop_notification(
                    user_id=u['id'],
                    mode=mode,
                    fare=fare,
                    target_fare=fare + 30,
                    saving=30.0,
                    meetup_id=meetup_id,
                    meetup_title=meetup_title,
                )
                ok(f"Extra demo notification #{nid} for {mode} mode to {u['full_name']}")

        # ──────────────────────────────────────────────────────────────
        step(7, "Verify notifications in database for all users")
        # ──────────────────────────────────────────────────────────────
        for u in users:
            all_notifs = Notification.get_by_user(u['id'])
            unread     = Notification.get_unread_count(u['id'])

            info(f"User {u['full_name']} (#{u['id']}): Total notifications: {len(all_notifs)}, Unread count: {unread}")

            print(f"\n{BOLD}  Recent Notifications for {u['full_name']}:{RESET}")
            print(f"  {'─' * 56}")
            for n in all_notifs[:4]:
                icon = '📉' if 'Fare Drop' in n['title'] else '🔔'
                read_status = '  ' if n['is_read'] else '🔴'
                time_str = n['created_at'].strftime('%H:%M:%S') if n.get('created_at') else '??:??'
                print(f"  {read_status} {icon} [{time_str}] {n['title']}")
                msg = n['message'][:70] + '…' if len(n['message']) > 70 else n['message']
                print(f"       {CYAN}{msg}{RESET}")
                if n.get('link'):
                    print(f"       🔗 {n['link']}")

        # ──────────────────────────────────────────────────────────────
        header("Test Complete ✅")
        # ──────────────────────────────────────────────────────────────
        print(f"""
  {GREEN}All tests passed!{RESET} Here's what to verify in the UI:

  1. Start the app:  {BOLD}python run.py{RESET}
  2. Log in as any user registered in the DB
  3. Check the 🔔 notification bell — badge will show the unread count
  4. Click notifications to see the fare-drop alerts
  5. Visit {BOLD}/fare-alert/{RESET} to see the alerts dashboard
  6. Visit {BOLD}/fare-alert/meetup/{meetup_id}{RESET} to see the meetup detail
""")


if __name__ == '__main__':
    main()
