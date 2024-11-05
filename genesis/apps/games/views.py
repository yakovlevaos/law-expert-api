from rest_framework.viewsets import ModelViewSet

from genesis.apps.games.models import (
    Game,
    Genre,
    Mode,
    Duration,
    Platform,
    Competencies,
    Author,
)
from genesis.apps.games.serializers import (
    GameSerializer,
    GenresSerializer,
    ModesSerializer,
    DurationSerializer,
    PlatformSerializer,
    CompetenciesSerializer,
    AuthorSerializer,
)


class GameViewSet(ModelViewSet):
    serializer_class = GameSerializer
    queryset = Game.objects.all()
    http_method_names = ["get", "head"]


class GenreViewSet(ModelViewSet):
    serializer_class = GenresSerializer
    queryset = Genre.objects.all()
    http_method_names = ["get", "head"]


class ModeViewSet(ModelViewSet):
    serializer_class = ModesSerializer
    queryset = Mode.objects.all()
    http_method_names = ["get", "head"]


class PlatformViewSet(ModelViewSet):
    serializer_class = PlatformSerializer
    queryset = Platform.objects.all()
    http_method_names = ["get", "head"]


class CompetitionViewSet(ModelViewSet):
    serializer_class = CompetenciesSerializer
    queryset = Competencies.objects.all()
    http_method_names = ["get", "head"]


class DurationViewSet(ModelViewSet):
    serializer_class = DurationSerializer
    queryset = Duration.objects.all()
    http_method_names = ["get", "head"]


class AuthorViewSet(ModelViewSet):
    serializer_class = AuthorSerializer
    queryset = Author.objects.all()
    http_method_names = ["get", "head"]
