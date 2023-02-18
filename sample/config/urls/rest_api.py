from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from drf_spectacular import views

urlpatterns = [
    path('v1/schema/', views.SpectacularAPIView.as_view(), name='schema'),
    path(
        'v1/schema/docs/',
        views.SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'v1/schema/redoc/',
        views.SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]

if settings.DEBUG:
    urlpatterns += [
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    ]
