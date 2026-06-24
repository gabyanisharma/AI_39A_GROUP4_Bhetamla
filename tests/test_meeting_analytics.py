import unittest
from datetime import date

from app.models.analytics import (
    split_upcoming_past, build_monthly_activity, summarize, _is_past,
)


class IsPastTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 18)

    def test_completed_is_past_regardless_of_date(self):
        self.assertTrue(_is_past({'status': 'completed',
                                  'meetup_date': date(2026, 12, 1)}, self.today))

    def test_cancelled_is_past(self):
        self.assertTrue(_is_past({'status': 'cancelled', 'meetup_date': None}, self.today))

    def test_past_date_is_past(self):
        self.assertTrue(_is_past({'status': 'planned',
                                  'meetup_date': date(2026, 6, 1)}, self.today))

    def test_future_date_is_not_past(self):
        self.assertFalse(_is_past({'status': 'planned',
                                   'meetup_date': date(2026, 6, 30)}, self.today))

    def test_today_is_not_past(self):
        self.assertFalse(_is_past({'status': 'planned',
                                   'meetup_date': self.today}, self.today))

    def test_no_date_planned_is_not_past(self):
        self.assertFalse(_is_past({'status': 'planned', 'meetup_date': None}, self.today))


class SplitUpcomingPastTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 18)
        self.meetups = [
            {'id': 1, 'meetup_date': date(2026, 6, 1), 'status': 'planned'},   # past
            {'id': 2, 'meetup_date': date(2026, 6, 30), 'status': 'planned'},  # upcoming
            {'id': 3, 'meetup_date': date(2026, 7, 15), 'status': 'planned'},  # upcoming
            {'id': 4, 'meetup_date': date(2026, 6, 30), 'status': 'completed'},  # past (completed)
        ]

    def test_partition_counts(self):
        upcoming, past = split_upcoming_past(self.meetups, self.today)
        self.assertEqual({m['id'] for m in upcoming}, {2, 3})
        self.assertEqual({m['id'] for m in past}, {1, 4})

    def test_upcoming_sorted_ascending(self):
        upcoming, _ = split_upcoming_past(self.meetups, self.today)
        self.assertEqual([m['id'] for m in upcoming], [2, 3])

    def test_empty_input(self):
        self.assertEqual(split_upcoming_past([], self.today), ([], []))


class MonthlyActivityTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 18)

    def test_returns_six_buckets_in_order(self):
        buckets = build_monthly_activity([], self.today, months=6)
        self.assertEqual(len(buckets), 6)
        self.assertEqual(buckets[-1]['month'], 6)   # current month last
        self.assertEqual(buckets[0]['month'], 1)    # Jan, six months back
        self.assertEqual([b['label'] for b in buckets],
                         ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'])

    def test_counts_land_in_correct_bucket(self):
        meetups = [
            {'meetup_date': date(2026, 6, 5)},
            {'meetup_date': date(2026, 6, 20)},
            {'meetup_date': date(2026, 4, 2)},
            {'meetup_date': date(2025, 12, 1)},  # outside 6-month window
        ]
        buckets = build_monthly_activity(meetups, self.today, months=6)
        by_month = {b['month']: b['count'] for b in buckets}
        self.assertEqual(by_month[6], 2)
        self.assertEqual(by_month[4], 1)
        self.assertEqual(sum(b['count'] for b in buckets), 3)  # Dec excluded

    def test_window_wraps_year_boundary(self):
        buckets = build_monthly_activity([], date(2026, 2, 10), months=6)
        self.assertEqual([(b['year'], b['month']) for b in buckets],
                         [(2025, 9), (2025, 10), (2025, 11), (2025, 12),
                          (2026, 1), (2026, 2)])


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 18)
        self.meetups = [
            {'id': 1, 'meetup_date': date(2026, 6, 1), 'status': 'completed', 'created_by': 10},
            {'id': 2, 'meetup_date': date(2026, 6, 30), 'status': 'planned', 'created_by': 10},
            {'id': 3, 'meetup_date': date(2026, 7, 15), 'status': 'planned', 'created_by': 99},
            {'id': 4, 'meetup_date': date(2026, 5, 2), 'status': 'cancelled', 'created_by': 99},
        ]

    def test_totals(self):
        s = summarize(self.meetups, self.today, user_id=10)
        self.assertEqual(s['total'], 4)
        self.assertEqual(s['upcoming'], 2)
        self.assertEqual(s['past'], 2)
        self.assertEqual(s['completed'], 1)
        self.assertEqual(s['cancelled'], 1)

    def test_hosted_vs_joined(self):
        s = summarize(self.meetups, self.today, user_id=10)
        self.assertEqual(s['hosted'], 2)
        self.assertEqual(s['joined'], 2)

    def test_completion_rate(self):
        # 1 completed of (1 completed + 1 cancelled) concluded = 50%
        s = summarize(self.meetups, self.today, user_id=10)
        self.assertEqual(s['completion_rate'], 50)

    def test_this_month_count(self):
        s = summarize(self.meetups, self.today, user_id=10)
        # June meetups: id 1 and id 2
        self.assertEqual(s['this_month'], 2)

    def test_no_conclusions_means_zero_rate(self):
        meetups = [{'id': 1, 'meetup_date': date(2026, 6, 30), 'status': 'planned', 'created_by': 10}]
        s = summarize(meetups, self.today, user_id=10)
        self.assertEqual(s['completion_rate'], 0)

    def test_empty(self):
        s = summarize([], self.today, user_id=10)
        self.assertEqual(s['total'], 0)
        self.assertEqual(s['completion_rate'], 0)


if __name__ == '__main__':
    unittest.main()
