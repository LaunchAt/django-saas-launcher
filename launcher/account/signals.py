from django.dispatch import Signal

signup = Signal(providing_args=['account', 'code'])

password_reset = Signal(providing_args=['account', 'code'])

email_change = Signal(providing_args=['account', 'code'])

phone_number_change = Signal(providing_args=['account', 'code'])
