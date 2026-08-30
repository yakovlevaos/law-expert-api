from django_filters import rest_framework as filters

from apps.games.models import (
    Author,
    Competency,
    Duration,
    Game,
    Genre,
    Mode,
    Platform,
)


class GameFilter(filters.FilterSet):
    """Catalog filters.

    Reference fields accept repeated ids (``?genres=1&genres=2``, matching any
    of them) and a case-insensitive name variant (``?genre=Песочница``).
    """

    genres = filters.ModelMultipleChoiceFilter(queryset=Genre.objects.all())
    platforms = filters.ModelMultipleChoiceFilter(queryset=Platform.objects.all())
    modes = filters.ModelMultipleChoiceFilter(queryset=Mode.objects.all())
    competencies = filters.ModelMultipleChoiceFilter(queryset=Competency.objects.all())
    duration_type = filters.ModelMultipleChoiceFilter(queryset=Duration.objects.all())
    author = filters.ModelMultipleChoiceFilter(queryset=Author.objects.all())

    # Playtime in hours. `endless=true` selects the games with no upper bound.
    duration_min = filters.NumberFilter(
        field_name="duration_hours_min", lookup_expr="gte"
    )
    duration_max = filters.NumberFilter(
        field_name="duration_hours_max", lookup_expr="lte"
    )
    endless = filters.BooleanFilter(
        field_name="duration_hours_min", lookup_expr="isnull"
    )

    genre = filters.CharFilter(field_name="genres__name", lookup_expr="iexact")
    platform = filters.CharFilter(field_name="platforms__name", lookup_expr="iexact")
    mode = filters.CharFilter(field_name="modes__name", lookup_expr="iexact")
    competency = filters.CharFilter(
        field_name="competencies__name", lookup_expr="iexact"
    )

    class Meta:
        model = Game
        fields = [
            "genres",
            "platforms",
            "modes",
            "competencies",
            "duration_type",
            "author",
            "duration_min",
            "duration_max",
            "endless",
        ]
