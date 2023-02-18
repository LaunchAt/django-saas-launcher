from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .admin import urlpatterns as admin_urlpatterns
from .rest_api import urlpatterns as rest_api_urlpatterns

urlpatterns = [
    path('admin/', include(admin_urlpatterns)),
    path('rest_api/', include(rest_api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += [
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    ]
