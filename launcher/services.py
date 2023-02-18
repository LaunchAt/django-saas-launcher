from typing import Any, List, Optional, Type

from django.db.models import Model, QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequestError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Bad request.')
    default_code = 'bad_request'


class UnauthorizedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Authentication credentials were not provided.')
    default_code = 'unauthorized'


class ForbiddenError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('You do not have permission to perform this action.')
    default_code = 'forbidden'


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('Not found.')
    default_code = 'not_found'


class BaseService:
    def __init__(self, *, model: Optional[Type[Model]] = None) -> None:
        self.model = model

    def bad_request(self, *, code: Optional[str] = None, detail: Any = None) -> None:
        raise BadRequestError(detail=detail, code=code)

    def unauthorized(self, *, code: Optional[str] = None, detail: Any = None) -> None:
        raise UnauthorizedError(detail=detail, code=code)

    def forbidden(self, *, code: Optional[str] = None, detail: Any = None) -> None:
        raise ForbiddenError(detail=detail, code=code)

    def not_found(self, *, code: Optional[str] = None, detail: Any = None) -> None:
        raise NotFoundError(detail=detail, code=code)

    def get_model(self) -> Type[Model]:
        assert self.model, _(
            'If you have not initialized a model class, you will not be '
            'able to access the `get_model` method of the Service class.'
        )
        return self.model

    def get_queryset(
        self,
        *,
        select_related: List[str] = [],
        prefetch_related: List[str] = [],
    ) -> QuerySet:
        model = self.get_model()
        queryset = model.objects.all()
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
