from django.forms.fields import CharField
from django.forms.widgets import Input

from .validators import PhoneNumberValidator

__all__ = ['PhoneNumberInput', 'PhoneNumberField']


class PhoneNumberInput(Input):
    input_type = 'tel'
    template_name = 'django/forms/widgets/input.html'


class PhoneNumberField(CharField):
    widget = PhoneNumberInput
    default_validators = [PhoneNumberValidator()]

    def __init__(self, **kwargs):
        super().__init__(strip=True, **kwargs)
