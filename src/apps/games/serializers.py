from rest_framework import serializers

from apps.games.models import (
    Author,
    Competency,
    Duration,
    Game,
    Genre,
    Mode,
    Platform,
    ScreenShot,
)


class NameSerializer(serializers.ModelSerializer):
    """Shared shape for every simple `name` reference model."""

    class Meta:
        fields = ["id", "name"]


class AuthorSerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Author


class DurationSerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Duration


class PlatformSerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Platform


class GenreSerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Genre


class CompetencySerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Competency


class ModeSerializer(NameSerializer):
    class Meta(NameSerializer.Meta):
        model = Mode


class ScreenShotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenShot
        fields = ["id", "screen_shot"]


class GameSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    duration_type = DurationSerializer()
    screen_shots_list = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    titles_list = serializers.SerializerMethodField()
    # Generated from the hour range; kept in the payload for compatibility.
    duration = serializers.CharField(read_only=True)
    genres = GenreSerializer(read_only=True, many=True)
    platforms = PlatformSerializer(read_only=True, many=True)
    competencies = CompetencySerializer(read_only=True, many=True)
    modes = ModeSerializer(read_only=True, many=True)

    class Meta:
        model = Game
        fields = [
            "id",
            "titles_list",
            "author",
            "description",
            "screen_shots_list",
            "cover_image",
            "duration",
            "duration_hours_min",
            "duration_hours_max",
            "duration_type",
            "genres",
            "competencies",
            "platforms",
            "modes",
        ]

    def _absolute_url(self, image) -> str | None:
        """Absolute URL for an image field, or None when no file is attached."""
        if not image:
            return None
        url = image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_screen_shots_list(self, obj) -> list[str]:
        return [
            url
            for url in (
                self._absolute_url(item.screen_shot) for item in obj.screen_shots.all()
            )
            if url
        ]

    def get_titles_list(self, obj) -> list[str]:
        return obj.titles_list

    def get_cover_image(self, obj) -> str | None:
        return self._absolute_url(obj.cover_image)
