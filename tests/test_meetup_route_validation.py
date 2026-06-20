import unittest

from app.models.meetup_route import validate_route_payload


class MeetupRouteValidationTest(unittest.TestCase):
    def test_valid_payload_returns_clean_waypoints_in_array_order(self):
        payload = {
            "travel_mode": "driving",
            "route_summary": {"distance_m": 1532.8, "duration_s": 420.2},
            "waypoints": [
                {
                    "sequence_index": 9,
                    "label": "Start",
                    "address": "Thamel, Kathmandu",
                    "latitude": "27.7153",
                    "longitude": "85.3123",
                    "source": "geocoder",
                },
                {
                    "label": "Stop",
                    "address": "New Road",
                    "latitude": 27.7041,
                    "longitude": 85.3145,
                    "source": "map_click",
                },
            ],
        }

        cleaned, errors = validate_route_payload(payload)

        self.assertEqual(errors, [])
        self.assertEqual(cleaned["travel_mode"], "driving")
        self.assertEqual(cleaned["distance_m"], 1533)
        self.assertEqual(cleaned["duration_s"], 420)
        self.assertEqual([wp["sequence_index"] for wp in cleaned["waypoints"]], [0, 1])
        self.assertEqual(cleaned["waypoints"][0]["label"], "Start")
        self.assertAlmostEqual(cleaned["waypoints"][0]["latitude"], 27.7153)

    def test_rejects_payload_with_too_few_waypoints(self):
        payload = {
            "travel_mode": "driving",
            "waypoints": [
                {"latitude": 27.7153, "longitude": 85.3123},
            ],
        }

        cleaned, errors = validate_route_payload(payload)

        self.assertIsNone(cleaned)
        self.assertIn("Add at least two stops before saving a route.", errors)

    def test_rejects_waypoints_outside_kathmandu_bounds(self):
        payload = {
            "travel_mode": "driving",
            "waypoints": [
                {"latitude": 27.7153, "longitude": 85.3123},
                {"latitude": 28.1000, "longitude": 85.3145},
            ],
        }

        cleaned, errors = validate_route_payload(payload)

        self.assertIsNone(cleaned)
        self.assertIn("Stop 2 is outside the Kathmandu planning area.", errors)

    def test_rejects_invalid_travel_mode(self):
        payload = {
            "travel_mode": "helicopter",
            "waypoints": [
                {"latitude": 27.7153, "longitude": 85.3123},
                {"latitude": 27.7041, "longitude": 85.3145},
            ],
        }

        cleaned, errors = validate_route_payload(payload)

        self.assertIsNone(cleaned)
        self.assertIn("Unsupported travel mode.", errors)


if __name__ == "__main__":
    unittest.main()
