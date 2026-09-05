"""Drop the old free-text duration column and add the new indexes/constraints."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0005_migrate_titles_and_durations"),
    ]

    operations = [
        # Giving the column a default before dropping it is what makes this
        # migration reversible: reversing RemoveField re-adds a NOT NULL column
        # to 144 existing rows, which fails without one. 0005 then replaces the
        # placeholders with the real strings.
        migrations.AlterField(
            model_name="game",
            name="duration",
            field=models.CharField(
                default="", max_length=255, verbose_name="Длительность"
            ),
        ),
        migrations.RemoveField(
            model_name="game",
            name="duration",
        ),
        migrations.AddIndex(
            model_name="game",
            index=models.Index(
                fields=["duration_hours_min"], name="game_duration_min_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="game",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("duration_hours_min__lte", models.F("duration_hours_max")),
                    ("duration_hours_min__isnull", True),
                    _connector="OR",
                ),
                name="game_duration_range_is_ordered",
            ),
        ),
        migrations.AddConstraint(
            model_name="alternativetitle",
            constraint=models.UniqueConstraint(
                fields=("game", "name"), name="alternative_title_unique_per_game"
            ),
        ),
    ]
