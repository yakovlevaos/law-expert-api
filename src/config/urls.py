from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("apps.games.urls")),
]

if settings.DEBUG:
    # debug_toolbar is a dev-only dependency, so it must not be imported at
    # module level -- the production image does not ship it.
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += [
        path(
            "api/v1/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="docs",
        ),
        path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += debug_toolbar_urls()
