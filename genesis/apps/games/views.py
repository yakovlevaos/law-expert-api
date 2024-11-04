from rest_framework.viewsets import ModelViewSet

from genesis.apps.games.models import Game
from genesis.apps.games.serializers import GameSerializer


class GameViewSet(ModelViewSet):
    serializer_class = GameSerializer
    queryset = Game.objects.all()
    http_method_names = ["get", "head"]
