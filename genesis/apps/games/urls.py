from django.urls import include, path
from rest_framework.routers import SimpleRouter

from genesis.apps.games.views import GameViewSet

router = SimpleRouter()
router.register("", GameViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
