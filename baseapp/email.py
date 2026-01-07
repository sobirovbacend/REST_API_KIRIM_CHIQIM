from django.core.mail import send_mail
from django.conf import settings

def send_email_code(email , code):
    send_mail(
        subject='Tasdiqlsh kodi',
        message=f'Sizning tasdiqlash kodingiz: {code}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list= [email],
        fail_silently= False
        )