"""Repair a corrupted game title.

"Crash Bandicoot 4: It's About Time" was stored as "... It's About duration",
the leftover of a careless find-and-replace of the word "Time" somewhere in the
catalog's history. Both tables are checked because the name may sit either on
the game itself or among its alternative titles.
"""

from django.db import migrations

BROKEN = "Crash Bandicoot 4: It’s About duration"
FIXED = "Crash Bandicoot 4: It’s About Time"


def _rename(apps, old, new):
    Game = apps.get_model("games", "Game")
    AlternativeTitle = apps.get_model("games", "AlternativeTitle")

    Game.objects.filter(title=old).update(title=new)
    AlternativeTitle.objects.filter(name=old).update(name=new)


def forwards(apps, schema_editor):
    _rename(apps, BROKEN, FIXED)


def backwards(apps, schema_editor):
    _rename(apps, FIXED, BROKEN)


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0006_drop_free_text_duration"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
