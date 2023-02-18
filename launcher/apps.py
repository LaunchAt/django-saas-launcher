from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LauncherConfig(AppConfig):
    name = 'launcher'
    verbose_name = _('launcher')
