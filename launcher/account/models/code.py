import base64

import pyotp
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from launcher.fields import PhoneNumberField
from launcher.models import BaseModel, BaseModelManager

User: AbstractBaseUser = get_user_model()


class VerificationCodeManager(BaseModelManager):
    pass


class VerificationCode(BaseModel):
    expiry_sec = 1800

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('user'))

    objects = VerificationCodeManager()

    class Meta:
        abstract = True

    def refresh(self):
        self.updated_at = now()
        return self.save(update_fields=['updated_at'])

    @property
    def is_expired(self):
        return self.updated_at.timestamp() + self.expiry_sec < now().timestamp()

    @property
    def six_digits_code(self):
        totp = pyotp.TOTP(self.base_32_code)
        return totp.generate_otp(totp.timecode(self.updated_at))

    @property
    def base_32_code(self):
        return base64.b32encode(self.id.bytes).decode('utf-8')


class EmailChangeCode(VerificationCode):
    email = models.EmailField(_('email address'))

    class Meta(VerificationCode.Meta):
        verbose_name = _('email change code')
        verbose_name_plural = _('email change codes')

    def refresh(self, email):
        self.email = email
        self.updated_at = now()
        return self.save(update_fields=['updated_at', 'email'])


class PasswordResetCode(VerificationCode):
    class Meta(VerificationCode.Meta):
        verbose_name = _('password reset code')
        verbose_name_plural = _('password reset codes')


class PhoneNumberChangeCode(VerificationCode):
    phone_number = PhoneNumberField(_('phone number'))

    class Meta(VerificationCode.Meta):
        verbose_name = _('phone number code')
        verbose_name_plural = _('phone number codes')

    def refresh(self, phone_number):
        self.phone_number = phone_number
        self.updated_at = now()
        return self.save(update_fields=['updated_at', 'phone_number'])


class SignupCode(VerificationCode):
    class Meta(VerificationCode.Meta):
        verbose_name = _('signup code')
        verbose_name_plural = _('signup codes')
