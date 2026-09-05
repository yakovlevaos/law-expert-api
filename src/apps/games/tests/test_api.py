from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.games.models import Game, Genre
from apps.games.tests.factories import make_author, make_game

LIST_ENDPOINTS = [
    "game-list",
    "genre-list",
    "mode-list",
    "platform-list",
    "competency-list",
    "duration-list",
    "author-list",
]


class ApiTestCase(TestCase):
    def setUp(self):
        # DRF throttling counts through the cache, which is shared between
        # tests in a single process.
        cache.clear()


class ListEndpointsTests(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        make_game("Alpha", author=make_author("Studio A"))
        make_game("Beta")

    def test_every_list_endpoint_is_paginated(self):
        for name in LIST_ENDPOINTS:
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    set(response.json()),
                    {"count", "next", "previous", "results"},
                )

    def test_game_detail(self):
        game = Game.objects.get(title="Alpha")
        response = self.client.get(reverse("game-detail", args=[game.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["titles_list"], ["Alpha"])

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class WriteMethodsTests(ApiTestCase):
    def test_write_methods_are_rejected(self):
        url = reverse("game-list")
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 405)


class SerializationTests(ApiTestCase):
    def test_image_urls_are_absolute(self):
        make_game("Alpha")
        payload = self.client.get(reverse("game-list")).json()["results"][0]
        self.assertTrue(payload["cover_image"].startswith("http://testserver/cdn/"))
        self.assertTrue(
            payload["screen_shots_list"][0].startswith("http://testserver/cdn/")
        )

    def test_missing_cover_image_does_not_break_serialization(self):
        game = make_game("Alpha")
        Game.objects.filter(pk=game.pk).update(cover_image="")
        response = self.client.get(reverse("game-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["results"][0]["cover_image"])


class OrderingTests(ApiTestCase):
    def _titles(self, **params):
        response = self.client.get(reverse("game-list"), params)
        self.assertEqual(response.status_code, 200)
        return [item["titles_list"][0] for item in response.json()["results"]]

    def test_series_titles_sort_by_the_name_after_the_prefix(self):
        make_game("Alpha")
        make_game("Серия игр Beta")
        make_game("Gamma")
        # "Серия игр Beta" sorts as "Beta", i.e. between Alpha and Gamma.
        self.assertEqual(self._titles(), ["Alpha", "Серия игр Beta", "Gamma"])

    def test_ordering_is_deterministic_for_equal_sort_keys(self):
        first = make_game("Alpha")
        second = make_game("Серия игр Alpha")
        # Both collapse to the same sort key; `id` must break the tie.
        self.assertEqual(self._titles(), ["Alpha", "Серия игр Alpha"])
        self.assertLess(first.pk, second.pk)

    def test_pagination_does_not_repeat_or_drop_rows(self):
        for index in range(7):
            make_game(f"Game {index}")
            make_game(f"Серия игр Game {index}")

        seen = []
        for page in (1, 2, 3):
            seen += self._titles(page=page, page_size=5)
        self.assertEqual(len(seen), 14)
        self.assertEqual(len(set(seen)), 14)

    def test_explicit_ordering_query_param(self):
        make_game("Beta")
        make_game("Alpha")
        self.assertEqual(self._titles(ordering="-title"), ["Beta", "Alpha"])


class FilteringTests(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        make_game("Shooter", genre="Шутер", platform="PC")
        make_game("Puzzle", genre="Головоломка", platform="PS5")

    def _titles(self, **params):
        response = self.client.get(reverse("game-list"), params)
        self.assertEqual(response.status_code, 200)
        return [item["titles_list"][0] for item in response.json()["results"]]

    def test_filter_by_genre_id(self):
        genre = Genre.objects.get(name="Шутер")
        self.assertEqual(self._titles(genres=genre.pk), ["Shooter"])

    def test_filter_by_genre_name(self):
        self.assertEqual(self._titles(genre="головоломка"), ["Puzzle"])

    def test_filter_by_multiple_genres_returns_each_game_once(self):
        ids = list(Genre.objects.values_list("pk", flat=True))
        response = self.client.get(reverse("game-list"), {"genres": ids})
        self.assertEqual(response.json()["count"], 2)

    def test_search_matches_title(self):
        self.assertEqual(self._titles(search="shoot"), ["Shooter"])

    def test_unknown_filter_value_is_rejected(self):
        response = self.client.get(reverse("game-list"), {"genres": 999999})
        self.assertEqual(response.status_code, 400)


class CachingTests(ApiTestCase):
    def test_read_responses_carry_cache_headers(self):
        make_game("Alpha")
        response = self.client.get(reverse("game-list"))
        self.assertIn("max-age", response.headers["Cache-Control"])
        self.assertIn("public", response.headers["Cache-Control"])
        self.assertIn("ETag", response.headers)

    def test_matching_etag_returns_304(self):
        make_game("Alpha")
        etag = self.client.get(reverse("game-list")).headers["ETag"]
        response = self.client.get(
            reverse("game-list"), headers={"if-none-match": etag}
        )
        self.assertEqual(response.status_code, 304)


class QueryCountTests(ApiTestCase):
    def test_game_list_query_count_does_not_grow_with_the_number_of_games(self):
        make_game("Game 0")
        with self.assertNumQueries(8):
            self.client.get(reverse("game-list"))

        for index in range(1, 12):
            make_game(f"Game {index}")
        # Same query count for 12 games as for one: no N+1.
        with self.assertNumQueries(8):
            self.client.get(reverse("game-list"))


class AlternativeTitleTests(ApiTestCase):
    def test_titles_list_contains_primary_then_alternatives_in_order(self):
        make_game(
            "Horizon Zero Dawn",
            alternative_titles=["Horizon Forbidden West", "Horizon Third"],
        )
        payload = self.client.get(reverse("game-list")).json()["results"][0]
        self.assertEqual(
            payload["titles_list"],
            ["Horizon Zero Dawn", "Horizon Forbidden West", "Horizon Third"],
        )

    def test_game_without_alternatives_returns_a_single_title(self):
        make_game("Alpha")
        payload = self.client.get(reverse("game-list")).json()["results"][0]
        self.assertEqual(payload["titles_list"], ["Alpha"])

    def test_search_matches_an_alternative_title(self):
        make_game("God of War", alternative_titles=["God of War: Ragnarok"])
        make_game("Other")
        response = self.client.get(reverse("game-list"), {"search": "Ragnarok"})
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["titles_list"][0], "God of War")

    def test_ordering_uses_the_primary_title_only(self):
        make_game("Beta", alternative_titles=["Aaa"])
        make_game("Alpha")
        titles = [
            item["titles_list"][0]
            for item in self.client.get(reverse("game-list")).json()["results"]
        ]
        self.assertEqual(titles, ["Alpha", "Beta"])


class DurationTests(ApiTestCase):
    def test_duration_string_is_generated_from_the_hour_range(self):
        cases = {
            "Single": ((10, 10), "10 часов"),
            "Few": ((3, 3), "3 часа"),
            "Teen": ((13, 13), "13 часов"),
            "Twenty two": ((22, 22), "22 часа"),
            "One": ((1, 1), "1 час"),
            "Range": ((5, 10), "5-10 часов"),
            "Endless": ((None, None), "∞"),
        }
        for title, (hours, _) in cases.items():
            make_game(title, duration_hours=hours)

        payload = {
            item["titles_list"][0]: item["duration"]
            for item in self.client.get(reverse("game-list")).json()["results"]
        }
        for title, (_, expected) in cases.items():
            with self.subTest(title=title):
                self.assertEqual(payload[title], expected)

    def test_hour_range_is_exposed(self):
        make_game("Alpha", duration_hours=(5, 10))
        payload = self.client.get(reverse("game-list")).json()["results"][0]
        self.assertEqual(payload["duration_hours_min"], 5)
        self.assertEqual(payload["duration_hours_max"], 10)

    def test_filter_by_minimum_hours(self):
        make_game("Short", duration_hours=(2, 2))
        make_game("Long", duration_hours=(40, 40))
        response = self.client.get(reverse("game-list"), {"duration_min": 10})
        self.assertEqual(
            [i["titles_list"][0] for i in response.json()["results"]], ["Long"]
        )

    def test_filter_by_maximum_hours(self):
        make_game("Short", duration_hours=(2, 2))
        make_game("Long", duration_hours=(40, 40))
        response = self.client.get(reverse("game-list"), {"duration_max": 10})
        self.assertEqual(
            [i["titles_list"][0] for i in response.json()["results"]], ["Short"]
        )

    def test_filter_endless_games(self):
        make_game("Endless", duration_hours=(None, None))
        make_game("Finite", duration_hours=(10, 10))
        response = self.client.get(reverse("game-list"), {"endless": "true"})
        self.assertEqual(
            [i["titles_list"][0] for i in response.json()["results"]], ["Endless"]
        )

    def test_ordering_by_duration(self):
        make_game("Long", duration_hours=(40, 40))
        make_game("Short", duration_hours=(2, 2))
        response = self.client.get(
            reverse("game-list"), {"ordering": "duration_hours_min"}
        )
        self.assertEqual(
            [i["titles_list"][0] for i in response.json()["results"]],
            ["Short", "Long"],
        )
