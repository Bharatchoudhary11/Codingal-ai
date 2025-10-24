from django.contrib import admin
from django.urls import include, path

from core.views import service_root

urlpatterns = [
    path("", service_root, name="service-root"),
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]
