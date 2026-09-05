from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.games.models import (
    AlternativeTitle,
    Author,
    Competency,
    Duration,
    Game,
    Genre,
    Mode,
    Platform,
    ScreenShot,
)


def image_preview(image, size: int) -> str:
    """Clickable thumbnail for an image field, or a dash when it is empty."""
    if not image:
        return "—"
    return format_html(
        '<a href="{}" target="_blank">'
        '<img src="{}" alt="{}" width="{}" height="{}" style="object-fit: cover;" />'
        "</a>",
        image.url,
        image.url,
        image.name,
        size,
        size,
    )


class CustomAdminFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        preview = image_preview(value, 100) if hasattr(value, "url") else ""
        return mark_safe(preview) + super().render(name, value, attrs, renderer)


class NameAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Author)
class AuthorAdmin(NameAdmin):
    pass


@admin.register(Genre)
class GenreAdmin(NameAdmin):
    pass


@admin.register(Platform)
class PlatformAdmin(NameAdmin):
    pass


@admin.register(Duration)
class DurationAdmin(NameAdmin):
    pass


@admin.register(Competency)
class CompetencyAdmin(NameAdmin):
    pass


@admin.register(Mode)
class ModeAdmin(NameAdmin):
    pass


class AlternativeTitleInline(admin.TabularInline):
    model = AlternativeTitle
    extra = 1


class ScreenShotInline(admin.TabularInline):
    model = ScreenShot
    extra = 1
    formfield_overrides = {models.ImageField: {"widget": CustomAdminFileWidget}}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    inlines = [AlternativeTitleInline, ScreenShotInline]
    formfield_overrides = {models.ImageField: {"widget": CustomAdminFileWidget}}

    list_display = ("title", "image_cover", "duration_display", "duration_type")
    list_select_related = ("author", "duration_type")
    list_filter = ("duration_type", "platforms", "modes", "genres")
    search_fields = ("title", "description", "alternative_titles__name")
    autocomplete_fields = ("author", "duration_type")
    filter_horizontal = ("genres", "competencies", "platforms", "modes")
    readonly_fields = ("created_at", "modified_at")

    @admin.display(description="Обложка")
    def image_cover(self, obj):
        return image_preview(obj.cover_image, 50)

    @admin.display(description="Длительность")
    def duration_display(self, obj):
        return obj.duration
