from apps.games.models import (
    AlternativeTitle,
    Author,
    Competency,
    Duration,
    Game,
    Genre,
    Mode,
    Platform,
    ScreenShot,
)


def make_game(
    title: str,
    *,
    genre: str = "Экшен",
    platform: str = "PC",
    alternative_titles: list[str] | None = None,
    duration_hours: tuple[int | None, int | None] = (10, 10),
    **kwargs,
):
    """Create a Game with its required relations.

    Image fields get a name but no file on disk -- `.url` only needs the name,
    and the tests never read the bytes.
    """
    duration, _ = Duration.objects.get_or_create(
        name=kwargs.pop("duration_name", "средняя")
    )
    game = Game(
        title=title,
        description=kwargs.pop("description", "Описание"),
        duration_hours_min=duration_hours[0],
        duration_hours_max=duration_hours[1],
        duration_type=duration,
        author=kwargs.pop("author", None),
    )
    game.cover_image.name = f"games/{abs(hash(title)) % 10**6}.jpg"
    game.save()

    game.genres.add(Genre.objects.get_or_create(name=genre)[0])
    game.platforms.add(Platform.objects.get_or_create(name=platform)[0])
    game.modes.add(Mode.objects.get_or_create(name="Одиночный")[0])
    game.competencies.add(Competency.objects.get_or_create(name="логика")[0])

    AlternativeTitle.objects.bulk_create(
        AlternativeTitle(game=game, name=name, position=position)
        for position, name in enumerate(alternative_titles or [], start=1)
    )

    screenshot = ScreenShot(game=game)
    screenshot.screen_shot.name = f"games/{game.pk}_1.jpg"
    screenshot.save()
    return game


def make_author(name: str) -> Author:
    return Author.objects.create(name=name)
