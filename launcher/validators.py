import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

__all__ = ['PhoneNumberValidator']


@deconstructible
class PhoneNumberValidator:
    message = _(
        '"%(value)s" value has an invalid format. It must be in '
        'full international format includes a plus sign (+) followed '
        'by the country code, city code, and local phone number.'
    )
    code = 'invalid_phone_number'

    def __init__(self, message=None, code=None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        try:
            parsed_number = phonenumbers.parse(str(value), None)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError(self.message, code=self.code, params={'value': value})
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError(self.message, code=self.code, params={'value': value})

    def __eq__(self, other):
        return (
            isinstance(other, PhoneNumberValidator)
            and self.message == other.message
            and self.code == other.code
        )


validate_phone_number = PhoneNumberValidator()
