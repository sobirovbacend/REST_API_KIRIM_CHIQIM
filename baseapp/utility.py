import re
from  rest_framework.exceptions import ValidationError

email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
phone_regex = re.compile(r'^(\+?998)[-\s]?\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}$')


def email_or_phone(email_phone_number):
    if re.fullmatch(email_regex, email_phone_number):
        data = 'email'

    elif re.fullmatch(phone_regex, email_phone_number):
        data = 'phone'

    else:
        data = {
            'success': False,
            'message': 'Telefon yoki emailda xato'
        }
        raise ValidationError(data)

    return data