from django_hosts import host, patterns

host_patterns = patterns(
    '',
    host('', 'config.urls', name='default'),
    host(r'admin(\.\w+)*', 'config.urls.admin', name='admin'),
    host(r'api(\.\w+)*', 'config.urls.rest_api', name='rest_api'),
)
