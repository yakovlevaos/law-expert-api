from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Case, F, TextField, When
from django.db.models.functions import Substr
from django.utils.cache import patch_cache_control
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.games.filters import GameFilter
from apps.games.models import (
    Author,
    Competency,
    Duration,
    Game,
    Genre,
    Mode,
    Platform,
)
from apps.games.serializers import (
    AuthorSerializer,
    CompetencySerializer,
    DurationSerializer,
    GameSerializer,
    GenreSerializer,
    ModeSerializer,
    PlatformSerializer,
)

if TYPE_CHECKING:
    # At runtime the mixin must stay a plain object so it can be combined with
    # any view; for type checkers it needs a base that declares the DRF hooks
    # it calls through `super()`.
    from rest_framework.views import APIView

    _ViewBase = APIView
else:
    _ViewBase = object


class CacheControlMixin(_ViewBase):
    """Adds a public Cache-Control to successful reads.

    The catalog is read-only, so responses are safe to cache. Combined with
    ConditionalGetMiddleware this also gives clients ETag/304 revalidation.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        max_age = settings.API_CACHE_SECONDS
        if (
            max_age > 0
            and request.method in ("GET", "HEAD")
            and response.status_code == 200
        ):
            patch_cache_control(response, public=True, max_age=max_age)
        return response


class NameReferenceViewSet(CacheControlMixin, ReadOnlyModelViewSet):
    """Base viewset for the simple `name` reference endpoints."""

    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class GameViewSet(CacheControlMixin, ReadOnlyModelViewSet):
    SERIES_PREFIX = "Серия игр "

    serializer_class = GameSerializer
    filterset_class = GameFilter
    search_fields = ["title", "description", "alternative_titles__name"]
    ordering_fields = ["title", "created_at", "duration_hours_min"]

    queryset = (
        Game.objects.select_related("author", "duration_type")
        .prefetch_related(
            "alternative_titles",
            "genres",
            "screen_shots",
            "modes",
            "platforms",
            "competencies",
        )
        .annotate(
            # Titles like "Серия игр Devil May Cry 1-5" sort under the series
            # name rather than under "С".
            sort_field=Case(
                When(
                    title__startswith=SERIES_PREFIX,
                    then=Substr("title", len(SERIES_PREFIX) + 1),
                ),
                default=F("title"),
                output_field=TextField(),
            ),
        )
        # `id` is the tie-breaker: without it equal sort_field values make
        # pagination non-deterministic and rows can repeat or go missing.
        .order_by("sort_field", "id")
    )


class GenreViewSet(NameReferenceViewSet):
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()


class ModeViewSet(NameReferenceViewSet):
    serializer_class = ModeSerializer
    queryset = Mode.objects.all()


class PlatformViewSet(NameReferenceViewSet):
    serializer_class = PlatformSerializer
    queryset = Platform.objects.all()


class CompetencyViewSet(NameReferenceViewSet):
    serializer_class = CompetencySerializer
    queryset = Competency.objects.all()


class DurationViewSet(NameReferenceViewSet):
    serializer_class = DurationSerializer
    queryset = Duration.objects.all()


class AuthorViewSet(NameReferenceViewSet):
    serializer_class = AuthorSerializer
    queryset = Author.objects.all()
