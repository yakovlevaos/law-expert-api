"""Move newline-packed titles and free-text playtime into the new columns."""

import re

from django.db import migrations

ENDLESS = "∞"

# Inlined rather than imported from apps.games.durations: a migration has to
# keep working even when the application code moves on.
_RANGE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)\s+час\S*$")
_SINGLE_RE = re.compile(r"^(\d+)\s+час\S*$")


def _parse_duration(text):
    text = (text or "").strip()
    if text == ENDLESS:
        return None, None
    match = _RANGE_RE.match(text)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = _SINGLE_RE.match(text)
    if match:
        return int(match.group(1)), int(match.group(1))
    raise ValueError(f"Unrecognised duration: {text!r}")


def _hours_word(hours):
    if hours % 100 in (11, 12, 13, 14):
        return "часов"
    if hours % 10 == 1:
        return "час"
    if hours % 10 in (2, 3, 4):
        return "часа"
    return "часов"


def _format_duration(hours_min, hours_max):
    if hours_min is None or hours_max is None:
        return ENDLESS
    if hours_min == hours_max:
        return f"{hours_min} {_hours_word(hours_min)}"
    return f"{hours_min}-{hours_max} часов"


def forwards(apps, schema_editor):
    Game = apps.get_model("games", "Game")
    AlternativeTitle = apps.get_model("games", "AlternativeTitle")

    alternatives = []
    for game in Game.objects.all().iterator():
        names = [line.strip() for line in game.title.split("\n") if line.strip()]
        game.title = names[0]
        alternatives += [
            AlternativeTitle(game=game, name=name, position=position)
            for position, name in enumerate(names[1:], start=1)
        ]

        game.duration_hours_min, game.duration_hours_max = _parse_duration(
            game.duration
        )
        game.save(update_fields=["title", "duration_hours_min", "duration_hours_max"])

    AlternativeTitle.objects.bulk_create(alternatives)


def backwards(apps, schema_editor):
    Game = apps.get_model("games", "Game")

    for game in Game.objects.all().iterator():
        names = list(
            game.alternative_titles.order_by("position", "id").values_list(
                "name", flat=True
            )
        )
        game.title = "\n".join([game.title, *names])
        game.duration = _format_duration(
            game.duration_hours_min, game.duration_hours_max
        )
        game.save(update_fields=["title", "duration"])
        game.alternative_titles.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0004_split_titles_and_numeric_duration"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
