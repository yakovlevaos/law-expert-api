from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.games.views import (
    GameViewSet,
    DurationViewSet,
    ModeViewSet,
    CompetenceViewSet,
    GenreViewSet,
    PlatformViewSet,
    AuthorViewSet,
)

router = SimpleRouter()
router.register("games", GameViewSet)
router.register("durations", DurationViewSet)
router.register("competencies", CompetenceViewSet)
router.register("genres", GenreViewSet)
router.register("modes", ModeViewSet)
router.register("platforms", PlatformViewSet)
router.register("authors", AuthorViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
