from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from launcher.fields import PhoneNumberField
from launcher.models import BaseModel, BaseModelManager
from launcher.validators import validate_phone_number

User: AbstractBaseUser = get_user_model()


def is_email(value):
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


def is_phone_number(value):
    try:
        validate_phone_number(value)
        return True
    except ValidationError:
        return False


class AccountManager(BaseModelManager):
    def get_by_natural_key(self, natural_key):
        if is_email(natural_key):
            queryset = self.filter(email=natural_key)
        elif is_phone_number(natural_key):
            queryset = self.filter(phone_number=natural_key)
        else:
            queryset = self.filter(username=natural_key)
        return queryset.active_set().select_related('user').get()


class Account(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='account',
        verbose_name=_('user'),
    )
    username = models.CharField(
        _('username'),
        max_length=128,
        blank=True,
        null=True,
        default=None,
    )
    email = models.EmailField(_('email address'), blank=True, null=True, default=None)
    is_verified = models.BooleanField(_('verification status'), default=False)
    password = models.CharField(_('password'), max_length=128)
    phone_number = PhoneNumberField(
        _('phone number'),
        blank=True,
        null=True,
        default=None,
    )

    objects = AccountManager()

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['username'],
                condition=Q(deleted_at__isnull=True),
                name='unique_active_username',
            ),
            models.UniqueConstraint(
                fields=['email'],
                condition=Q(deleted_at__isnull=True),
                name='unique_active_email',
            ),
            models.UniqueConstraint(
                fields=['phone_number'],
                condition=Q(deleted_at__isnull=True),
                name='unique_active_phone_number',
            ),
            models.CheckConstraint(
                check=~Q(email__isnull=True, phone_number__isnull=True),
                name='not_both_email_and_phone_number_null',
            ),
        ]
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
