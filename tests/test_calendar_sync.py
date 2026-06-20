import unittest
from datetime import date, datetime, time
from importlib import import_module


def calendar_sync_module():
    try:
        return import_module('app.models.calendar_sync')
    except ModuleNotFoundError as exc:
        raise AssertionError('Calendar Sync backend module is missing') from exc


class CalendarProviderTest(unittest.TestCase):
    def test_normalizes_supported_provider_names(self):
        calendar_sync = calendar_sync_module()

        self.assertEqual(calendar_sync.normalize_provider('Google Calendar'), 'google')
        self.assertEqual(calendar_sync.normalize_provider('outlook'), 'outlook')
        self.assertEqual(calendar_sync.normalize_provider('Apple iCal'), 'apple')
        self.assertEqual(calendar_sync.normalize_provider('School Calendar'), 'other')


class IcsImportTest(unittest.TestCase):
    def test_parses_timed_and_all_day_events(self):
        calendar_sync = calendar_sync_module()
        ics_text = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:work-1
SUMMARY:Project Review
DTSTART:20260619T093000
DTEND:20260619T103000
LOCATION:Room 4
DESCRIPTION:Bring notes
END:VEVENT
BEGIN:VEVENT
UID:holiday-1
SUMMARY:College Holiday
DTSTART;VALUE=DATE:20260620
DTEND;VALUE=DATE:20260621
END:VEVENT
END:VCALENDAR
"""

        events = calendar_sync.parse_ics_events(ics_text)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['external_uid'], 'work-1')
        self.assertEqual(events[0]['title'], 'Project Review')
        self.assertEqual(events[0]['starts_at'], datetime(2026, 6, 19, 9, 30))
        self.assertEqual(events[0]['ends_at'], datetime(2026, 6, 19, 10, 30))
        self.assertEqual(events[0]['location'], 'Room 4')
        self.assertFalse(events[0]['is_all_day'])
        self.assertTrue(events[1]['is_all_day'])


class CalendarConflictTest(unittest.TestCase):
    def test_detects_imported_event_overlapping_meetup(self):
        calendar_sync = calendar_sync_module()
        meetups = [
            {
                'id': 7,
                'title': 'Team Lunch',
                'meetup_date': date(2026, 6, 19),
                'meetup_time': time(10, 0),
                'midpoint_address': 'Thamel',
            },
            {
                'id': 8,
                'title': 'Evening Walk',
                'meetup_date': date(2026, 6, 20),
                'meetup_time': time(18, 0),
            },
        ]
        imported_events = [
            {
                'id': 11,
                'title': 'Project Review',
                'starts_at': datetime(2026, 6, 19, 9, 30),
                'ends_at': datetime(2026, 6, 19, 10, 30),
                'account_email': 'student@example.com',
            },
            {
                'id': 12,
                'title': 'Dinner',
                'starts_at': datetime(2026, 6, 19, 20, 0),
                'ends_at': datetime(2026, 6, 19, 21, 0),
                'account_email': 'student@example.com',
            },
        ]

        conflicts = calendar_sync.find_calendar_conflicts(meetups, imported_events)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['meetup_id'], 7)
        self.assertEqual(conflicts[0]['meetup_title'], 'Team Lunch')
        self.assertEqual(conflicts[0]['event_title'], 'Project Review')
        self.assertEqual(conflicts[0]['account_email'], 'student@example.com')


class CalendarExportTest(unittest.TestCase):
    def test_builds_ics_export_for_user_meetups(self):
        calendar_sync = calendar_sync_module()
        meetups = [
            {
                'id': 4,
                'title': 'Coffee, Chat',
                'description': 'Discuss plans; confirm route',
                'meetup_date': date(2026, 6, 19),
                'meetup_time': time(14, 15),
                'winning_venue_name': 'Cafe Soma',
                'midpoint_address': 'Pulchowk',
            },
            {
                'id': 5,
                'title': 'Undated draft',
                'meetup_date': None,
                'meetup_time': None,
            },
        ]

        ics = calendar_sync.build_meetups_ics(
            meetups,
            now=datetime(2026, 6, 18, 12, 0),
            calendar_name='Bhetamla Test',
        )

        self.assertIn('BEGIN:VCALENDAR', ics)
        self.assertIn('X-WR-CALNAME:Bhetamla Test', ics)
        self.assertIn('UID:meetup-4@bhetamla', ics)
        self.assertIn('SUMMARY:Coffee\\, Chat', ics)
        self.assertIn('DESCRIPTION:Discuss plans\\; confirm route', ics)
        self.assertIn('LOCATION:Cafe Soma', ics)
        self.assertIn('DTSTART:20260619T141500', ics)
        self.assertNotIn('meetup-5@bhetamla', ics)


if __name__ == '__main__':
    unittest.main()
