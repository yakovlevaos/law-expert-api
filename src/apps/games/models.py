from typing import TYPE_CHECKING

from django.db import models

from apps.games.durations import format_duration


class NameBase(models.Model):
    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"


class Genre(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"


class Mode(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Режим"
        verbose_name_plural = "Режимы"


class Competency(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"


class Duration(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Длительность"
        verbose_name_plural = "Длительности"


class Platform(NameBase):
    class Meta(NameBase.Meta):
        verbose_name = "Платформа"
        verbose_name_plural = "Платформы"


class Game(models.Model):
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="games",
        verbose_name="Автор",
    )
    title = models.CharField("Название", max_length=255, unique=True)
    # null=True is kept deliberately: existing rows already hold NULLs.
    description = models.TextField("Описание", null=True, blank=True)  # noqa: DJ001
    cover_image = models.ImageField("Обложка", upload_to="games/")
    # Playtime as a range in hours; both NULL means "endless" (∞).
    duration_hours_min = models.PositiveIntegerField(
        "Длительность от, ч", null=True, blank=True
    )
    duration_hours_max = models.PositiveIntegerField(
        "Длительность до, ч", null=True, blank=True
    )
    duration_type = models.ForeignKey(
        Duration,
        on_delete=models.PROTECT,
        related_name="games",
        verbose_name="Тип длительности",
    )
    genres = models.ManyToManyField(Genre, verbose_name="Жанры")
    competencies = models.ManyToManyField(Competency, verbose_name="Компетенции")
    platforms = models.ManyToManyField(Platform, verbose_name="Платформы")
    modes = models.ManyToManyField(Mode, verbose_name="Режимы")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        # Reverse accessors Django creates at class-definition time; declaring
        # them keeps type checkers (which cannot see that) accurate.
        alternative_titles: models.Manager["AlternativeTitle"]
        screen_shots: models.Manager["ScreenShot"]

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["created_at"], name="game_created_at_idx"),
            models.Index(fields=["duration_hours_min"], name="game_duration_min_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    duration_hours_min__lte=models.F("duration_hours_max")
                )
                | models.Q(duration_hours_min__isnull=True),
                name="game_duration_range_is_ordered",
            ),
        ]

    def __str__(self):
        return str(self.title)

    @property
    def duration(self) -> str:
        """Human readable playtime, generated from the hour range."""
        return format_duration(self.duration_hours_min, self.duration_hours_max)

    @property
    def titles_list(self) -> list[str]:
        """Primary title followed by any alternative titles."""
        return [self.title, *(item.name for item in self.alternative_titles.all())]


class ScreenShot(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="screen_shots",
        verbose_name="Игра",
    )
    screen_shot = models.ImageField("Скриншот", upload_to="games/")

    if TYPE_CHECKING:
        # The implicit column Django adds alongside the `game` ForeignKey.
        game_id: int

    class Meta:
        verbose_name = "Скриншот"
        verbose_name_plural = "Скриншоты"
        ordering = ["id"]

    def __str__(self):
        return f"{self.game_id}: {self.screen_shot.name}"


class AlternativeTitle(models.Model):
    """An extra name a game is also known by.

    These used to be crammed into `Game.title` separated by newlines and split
    back apart in the serializer.
    """

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="alternative_titles",
        verbose_name="Игра",
    )
    name = models.CharField("Название", max_length=255)
    position = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Альтернативное название"
        verbose_name_plural = "Альтернативные названия"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "name"], name="alternative_title_unique_per_game"
            ),
        ]

    def __str__(self):
        return self.name
