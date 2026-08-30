from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.games.views import (
    AuthorViewSet,
    CompetencyViewSet,
    DurationViewSet,
    GameViewSet,
    GenreViewSet,
    ModeViewSet,
    PlatformViewSet,
)

router = SimpleRouter()
router.register("games", GameViewSet)
router.register("durations", DurationViewSet)
router.register("competencies", CompetencyViewSet)
router.register("genres", GenreViewSet)
router.register("modes", ModeViewSet)
router.register("platforms", PlatformViewSet)
router.register("authors", AuthorViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
