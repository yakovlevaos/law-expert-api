"""Schema for the new title and playtime model.

`Game.title` used to hold several names separated by newlines, which the
serializer split apart on every request; `Game.duration` was free text
("10 часов") that could not be filtered or sorted.

The change is split across three migrations because Postgres refuses to ALTER
a table that has pending trigger events from row updates in the same
transaction: 0004 adds the new schema, 0005 moves the data, 0006 drops the old
column.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0003_alter_author_options_alter_competency_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlternativeTitle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                (
                    "position",
                    models.PositiveIntegerField(default=0, verbose_name="Порядок"),
                ),
            ],
            options={
                "verbose_name": "Альтернативное название",
                "verbose_name_plural": "Альтернативные названия",
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddField(
            model_name="alternativetitle",
            name="game",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alternative_titles",
                to="games.game",
                verbose_name="Игра",
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="duration_hours_max",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Длительность до, ч"
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="duration_hours_min",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Длительность от, ч"
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="title",
            field=models.CharField(
                max_length=255, unique=True, verbose_name="Название"
            ),
        ),
    ]
