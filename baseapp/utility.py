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




EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
)

# Uzbekistan phone formatlari:
# +998901234567
# 998901234567
# 901234567
PHONE_REGEX = re.compile(
    r'^(\+998|998)?[0-9]{9}$'
)


# =========================
# EMAIL or PHONE CHECK
# =========================

def email_or_phone(value: str) -> str:
    """
    Foydalanuvchi email yoki telefon kiritganini aniqlaydi
    """
    if not value:
        return None

    value = value.strip()

    if EMAIL_REGEX.match(value):
        return 'email'

    if PHONE_REGEX.match(value):
        return 'phone'

    return None


# =========================
# PHONE NORMALIZER
# =========================

def normalize_phone(phone: str) -> str:
    """
    Telefon raqamni +998XXXXXXXXX formatga keltiradi
    """
    phone = phone.strip()

    if phone.startswith('+998'):
        return phone

    if phone.startswith('998'):
        return f'+{phone}'

    if len(phone) == 9:
        return f'+998{phone}'

    raise ValidationError({
        'success': False,
        'message': 'Telefon raqam noto‘g‘ri formatda'
    })
