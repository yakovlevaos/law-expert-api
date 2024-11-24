from django.db.models import Case, When, TextField
from django.db.models.functions import Substr
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from apps.games.models import (
    Game,
    Genre,
    Mode,
    Duration,
    Platform,
    Competencies,
    Author,
)
from apps.games.serializers import (
    GameSerializer,
    GenresSerializer,
    ModesSerializer,
    DurationSerializer,
    PlatformSerializer,
    CompetenciesSerializer,
    AuthorSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 200


class GameViewSet(ModelViewSet):
    START_FOR_SUBSTR = "Серия игр "
    queryset = (
        Game.objects.select_related(
            "author",
            "duration_type",
        )
        .annotate(
            sort_field=Case(
                When(
                    title__startswith=START_FOR_SUBSTR,
                    then=Substr("title", 11),
                ),
                output_field=TextField(),
                default="title",
            ),
        )
        .prefetch_related(
            "genres",
            "screen_shots",
            "modes",
            "platforms",
            "competencies",
        )
        .all()
        .order_by("sort_field")
    )
    serializer_class = GameSerializer

    http_method_names = ["get", "head"]
    pagination_class = StandardResultsSetPagination


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


class CompetenceViewSet(ModelViewSet):
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
