import unittest
from datetime import datetime, date, time

from app.models.notification_preference import (
    build_smart_alerts, _in_quiet_hours, _as_date, _as_time, DEFAULT_PREFERENCES,
)


def _prefs(**overrides):
    return {**DEFAULT_PREFERENCES, **overrides}


class QuietHoursTest(unittest.TestCase):
    def test_no_quiet_window_when_unset(self):
        self.assertFalse(_in_quiet_hours(3, None, None))

    def test_same_day_window(self):
        self.assertTrue(_in_quiet_hours(13, 9, 17))
        self.assertFalse(_in_quiet_hours(8, 9, 17))
        self.assertFalse(_in_quiet_hours(17, 9, 17))  # end is exclusive

    def test_overnight_window_wraps_midnight(self):
        self.assertTrue(_in_quiet_hours(23, 22, 7))
        self.assertTrue(_in_quiet_hours(2, 22, 7))
        self.assertFalse(_in_quiet_hours(12, 22, 7))


class CoercionTest(unittest.TestCase):
    def test_as_date_handles_str_and_date(self):
        self.assertEqual(_as_date('2026-06-18'), date(2026, 6, 18))
        self.assertEqual(_as_date(date(2026, 6, 18)), date(2026, 6, 18))
        self.assertEqual(_as_date(datetime(2026, 6, 18, 9)), date(2026, 6, 18))
        self.assertIsNone(_as_date('not-a-date'))

    def test_as_time_handles_str(self):
        self.assertEqual(_as_time('14:30:00'), time(14, 30))
        self.assertEqual(_as_time('09:05'), time(9, 5))


class BuildSmartAlertsTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 6, 18, 10, 0)  # Thu 18 Jun 2026, 10:00

    def test_disabled_returns_nothing(self):
        meetups = [{'id': 1, 'title': 'X', 'meetup_date': date(2026, 6, 18)}]
        alerts = build_smart_alerts(meetups, [], _prefs(smart_alerts_enabled=False), self.now)
        self.assertEqual(alerts, [])

    def test_quiet_hours_suppresses_everything(self):
        meetups = [{'id': 1, 'title': 'X', 'meetup_date': date(2026, 6, 18)}]
        prefs = _prefs(quiet_hours_start=9, quiet_hours_end=12)
        self.assertEqual(build_smart_alerts(meetups, [], prefs, self.now), [])

    def test_meetup_today_fires_today_alert(self):
        meetups = [{'id': 7, 'title': 'Coffee', 'meetup_date': date(2026, 6, 18),
                    'meetup_time': time(15, 0), 'status': 'planned'}]
        alerts = build_smart_alerts(meetups, [], _prefs(), self.now)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['key'], 'meetup_today:7:2026-06-18')
        self.assertIn('today', alerts[0]['message'].lower())
        self.assertEqual(alerts[0]['link'], '/meetup/view/7')

    def test_upcoming_within_lead_window_fires_reminder(self):
        # Tomorrow at 09:00 → ~23h away, inside default 24h lead.
        meetups = [{'id': 9, 'title': 'Lunch', 'meetup_date': date(2026, 6, 19),
                    'meetup_time': time(9, 0), 'status': 'planned'}]
        alerts = build_smart_alerts(meetups, [], _prefs(), self.now)
        self.assertEqual(len(alerts), 1)
        self.assertTrue(alerts[0]['key'].startswith('meetup_reminder:9:'))

    def test_upcoming_beyond_lead_window_is_silent(self):
        # Five days out, beyond a 24h lead.
        meetups = [{'id': 9, 'title': 'Lunch', 'meetup_date': date(2026, 6, 23),
                    'meetup_time': time(9, 0), 'status': 'planned'}]
        self.assertEqual(build_smart_alerts(meetups, [], _prefs(), self.now), [])

    def test_larger_lead_window_catches_further_meetups(self):
        meetups = [{'id': 9, 'title': 'Lunch', 'meetup_date': date(2026, 6, 20),
                    'meetup_time': time(9, 0), 'status': 'planned'}]
        prefs = _prefs(reminder_lead_hours=72)
        alerts = build_smart_alerts(meetups, [], prefs, self.now)
        self.assertEqual(len(alerts), 1)

    def test_completed_meetup_does_not_remind(self):
        meetups = [{'id': 1, 'title': 'Old', 'meetup_date': date(2026, 6, 18),
                    'status': 'completed'}]
        self.assertEqual(build_smart_alerts(meetups, [], _prefs(), self.now), [])

    def test_reminders_toggle_off(self):
        meetups = [{'id': 7, 'title': 'Coffee', 'meetup_date': date(2026, 6, 18),
                    'status': 'planned'}]
        prefs = _prefs(meetup_reminders=False)
        self.assertEqual(build_smart_alerts(meetups, [], prefs, self.now), [])

    def test_pending_invite_fires_when_enabled(self):
        invites = [{'invite_id': 4, 'meetup_id': 22, 'title': 'Hike',
                    'inviter_name': 'Asha'}]
        alerts = build_smart_alerts([], invites, _prefs(), self.now)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['key'], 'invite_pending:4')
        self.assertIn('Asha', alerts[0]['message'])
        self.assertEqual(alerts[0]['link'], '/meetup/view/22')

    def test_invite_toggle_off(self):
        invites = [{'invite_id': 4, 'meetup_id': 22, 'title': 'Hike', 'inviter_name': 'Asha'}]
        prefs = _prefs(invite_alerts=False)
        self.assertEqual(build_smart_alerts([], invites, prefs, self.now), [])

    def test_trending_digest_fires_with_count(self):
        alerts = build_smart_alerts([], [], _prefs(), self.now, trending_count=8)
        digest = [a for a in alerts if a['key'].startswith('trending_digest:')]
        self.assertEqual(len(digest), 1)
        self.assertIn('8', digest[0]['message'])

    def test_trending_digest_silent_without_count(self):
        alerts = build_smart_alerts([], [], _prefs(), self.now, trending_count=0)
        self.assertEqual(alerts, [])

    def test_keys_are_unique_per_run(self):
        meetups = [
            {'id': 7, 'title': 'A', 'meetup_date': date(2026, 6, 18), 'status': 'planned'},
            {'id': 8, 'title': 'B', 'meetup_date': date(2026, 6, 19),
             'meetup_time': time(9, 0), 'status': 'planned'},
        ]
        invites = [{'invite_id': 4, 'meetup_id': 22, 'title': 'Hike', 'inviter_name': 'Asha'}]
        alerts = build_smart_alerts(meetups, invites, _prefs(), self.now, trending_count=3)
        keys = [a['key'] for a in alerts]
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == '__main__':
    unittest.main()
