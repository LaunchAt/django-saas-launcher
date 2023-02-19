import uuid

from django.db import models
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

__all__ = ['BaseModelQuerySet', 'BaseModelManager', 'BaseModel']


class BaseModelQuerySet(QuerySet):
    def soft_delete(self):
        return self.update(deleted_at=now())

    def restore(self):
        return self.update(deleted_at=None)

    def active_set(self):
        return self.filter(deleted_at__isnull=True)


class BaseModelManager(BaseManager.from_queryset(BaseModelQuerySet)):  # type: ignore
    pass


class BaseModel(models.Model):
    id = models.UUIDField(_('uuid'), primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(
        _('created datetime'),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )
    updated_at = models.DateTimeField(
        _('updated datetime'),
        auto_now=True,
        editable=False,
    )
    deleted_at = models.DateTimeField(
        _('deleted datetime'),
        null=True,
        db_index=True,
        default=None,
        editable=False,
    )

    objects = BaseModelManager()

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        if self.deleted_at is None:
            self.deleted_at = now()
            self.save(update_fields=['deleted_at'])
            return True
        return False

    def restore(self):
        if self.deleted_at is not None:
            self.deleted_at = None
            self.save(update_fields=['deleted_at'])
            return True
        return False

    def update(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs.get(key))
        self.save(update_fields=list(set(['updated_at', *kwargs.keys()])))
        return self
