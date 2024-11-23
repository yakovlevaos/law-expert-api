from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.utils.html import format_html

from apps.games.models import (
    Author,
    Genre,
    Platform,
    Game,
    Duration,
    ScreenShot,
    Competencies,
    Mode,
)


class CustomAdminFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        result = []
        if hasattr(value, "url"):
            result.append(
                f"""<a href="{value.url}" target="_blank">
                      <img 
                        src="{value.url}" alt="{value}" 
                        width="100" height="100"
                        style="object-fit: cover;"
                      />
                    </a>"""
            )
        result.append(super().render(name, value, attrs, renderer))
        return format_html("".join(result))


@admin.register(Author)
class GameAuthorAdmin(admin.ModelAdmin):
    list_display = ["name"]
    readonly_fields = ["id"]


class ShowPhotoInline(admin.TabularInline):
    model = ScreenShot
    formfield_overrides = {models.ImageField: {"widget": CustomAdminFileWidget}}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    inlines = [ShowPhotoInline]
    formfield_overrides = {models.ImageField: {"widget": CustomAdminFileWidget}}

    list_display = ("title", "image_cover")

    def image_cover(self, obj):
        return format_html(
            f"""<a href="{obj.cover_image.url}" target="_blank">
                      <img 
                        src="{obj.cover_image.url}" alt="{obj.cover_image}" 
                        width="50" height="50"
                        style="object-fit: cover;"
                      />
                    </a>"""
        )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    pass


@admin.register(Duration)
class DurationAdmin(admin.ModelAdmin):
    pass


@admin.register(Competencies)
class CompetenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Mode)
class ModeAdmin(admin.ModelAdmin):
    pass
