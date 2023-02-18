from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

admin.site.site_header = '管理サイト'

admin.site.site_title = '管理サイト'

admin.site.index_title = 'ダッシュボード'

urlpatterns = [path('', admin.site.urls)]

if settings.DEBUG:
    urlpatterns = [
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        *urlpatterns,
    ]
