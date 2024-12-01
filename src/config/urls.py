from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.games.urls")),
]

if settings.DEBUG:
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
