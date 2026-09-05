from django.test import SimpleTestCase

from apps.games.durations import format_duration, parse_duration


class ParseDurationTests(SimpleTestCase):
    def test_single_value(self):
        self.assertEqual(parse_duration("10 часов"), (10, 10))
        self.assertEqual(parse_duration("3 часа"), (3, 3))

    def test_range(self):
        self.assertEqual(parse_duration("5-10 часов"), (5, 10))
        self.assertEqual(parse_duration("15 - 30 часов"), (15, 30))

    def test_endless(self):
        self.assertEqual(parse_duration("∞"), (None, None))

    def test_unrecognised_value_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("пара вечеров")


class FormatDurationTests(SimpleTestCase):
    def test_russian_plural_forms(self):
        self.assertEqual(format_duration(1, 1), "1 час")
        self.assertEqual(format_duration(3, 3), "3 часа")
        self.assertEqual(format_duration(5, 5), "5 часов")
        self.assertEqual(format_duration(13, 13), "13 часов")
        self.assertEqual(format_duration(22, 22), "22 часа")
        self.assertEqual(format_duration(100, 100), "100 часов")

    def test_range_and_endless(self):
        self.assertEqual(format_duration(5, 10), "5-10 часов")
        self.assertEqual(format_duration(None, None), "∞")


class RoundTripTests(SimpleTestCase):
    def test_every_stored_form_survives_a_round_trip(self):
        # These are the shapes the seeded catalog actually contains.
        samples = [
            "∞",
            "2 часа",
            "3 часа",
            "5 часов",
            "10 часов",
            "13 часов",
            "22 часа",
            "23 часа",
            "100 часов",
            "4-6 часов",
            "5-10 часов",
            "15-30 часов",
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(format_duration(*parse_duration(text)), text)
