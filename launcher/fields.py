import phonenumbers
from django.core.exceptions import ValidationError
from django.db.models import CharField
from django.utils.translation import gettext_lazy as _

from .forms import PhoneNumberField as PhoneNumberFormField
from .validators import PhoneNumberValidator

__all__ = ['PhoneNumberField']


class PhoneNumberField(CharField):
    default_validators = [PhoneNumberValidator()]
    description = _('International Phone number')
    default_error_messages = {
        'invalid': _(
            '"%(value)s" value has an invalid format. It must be in '
            'full international format includes a plus sign (+) followed '
            'by the country code, city code, and local phone number.'
        ),
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 32)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value
        try:
            parsed_number = phonenumbers.parse(str(value), None)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid_phone_number',
                params={'value': value},
            )
        else:
            return parsed_number

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        if not isinstance(value, phonenumbers.PhoneNumber):
            try:
                parsed_number = phonenumbers.parse(str(value), None)
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError(
                    self.error_messages['invalid'],
                    code='invalid_phone_number',
                    params={'value': value},
                )
            else:
                value = parsed_number
        return phonenumbers.format_number(value, phonenumbers.PhoneNumberFormat.E164)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                'form_class': PhoneNumberFormField,
                **kwargs,
            }
        )
