from rest_framework.pagination import CursorPagination as BaseCursorPagination
from rest_framework.settings import api_settings


class CursorPagination(BaseCursorPagination):
    cursor_query_param = 'cursor'
    page_size = api_settings.PAGE_SIZE or 10
    ordering = None
    page_size_query_param = 'page_size'
    max_page_size = 100
    offset_cutoff = None
