from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("404/", views.page_not_found),
    path("500/", views.server_error),
    path("admin/", admin.site.urls),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("about/", include("about.urls", namespace="about")),
    path("", include("posts.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "yatube.views.page_not_found"  # noqa
handler500 = "yatube.views.server_error"  # noqa

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)
