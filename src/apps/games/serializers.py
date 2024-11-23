from rest_framework import serializers

from apps.games.models import Author, Game, ScreenShot, Duration, Platform, Mode


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [
            "id",
            "name",
        ]


class ScreenSotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenShot
        fields = [
            "id",
            "screen_shot",
        ]


class DurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duration
        fields = [
            "id",
            "name",
        ]


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = [
            "id",
            "name",
        ]


class GenresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duration
        fields = [
            "id",
            "name",
        ]


class CompetenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duration
        fields = [
            "id",
            "name",
        ]


class ModesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mode
        fields = [
            "id",
            "name",
        ]


class GameSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    duration_type = DurationSerializer()
    screen_shots_list = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    titles_list = serializers.SerializerMethodField()
    genres = GenresSerializer(read_only=True, many=True)
    platforms = PlatformSerializer(read_only=True, many=True)
    competencies = CompetenciesSerializer(read_only=True, many=True)
    modes = ModesSerializer(read_only=True, many=True)

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
            "duration_type",
            "genres",
            "competencies",
            "platforms",
            "modes",
        ]

    def get_screen_shots_list(self, obj) -> list[str]:
        urls = []
        for item in obj.screen_shots.all():
            urls.append(item.screen_shot.url)
        return urls

    def get_titles_list(self, obj) -> list[str]:
        titles = [x.strip() for x in obj.title.split("\n")]
        return titles

    def get_cover_image(self, obj) -> str:
        return obj.cover_image.url
