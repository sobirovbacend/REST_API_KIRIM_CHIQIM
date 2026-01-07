from django.db import models
import random
from datetime import timedelta, datetime
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from rest_framework_simplejwt.tokens import RefreshToken
from baseapp.models import BaseModel
from config.settings import AUTH_USER_MODEL, EXPIRATION_EMAIL, EXPIRATION_PHONE
import uuid

ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user', 'manager', 'admin')
NEW, CODE_VERIFIED, DONE, PHOTO_DONE = ('new', 'code_verified', 'done', 'photo_done')
VIA_EMAIL, VIA_PHONE = ('via_email', 'via_phone')


class User(AbstractUser, BaseModel):
    USER_ROLE = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )

    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_DONE, PHOTO_DONE),
    )

    AUTH_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )

    user_role = models.CharField(max_length=30, choices=USER_ROLE, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=30, choices=AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=30, choices=AUTH_TYPE)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    photo = models.ImageField(
        upload_to='user_photos/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['.jpg', '.png', '.jpeg'])]
    )

    def __str__(self):
        return self.username

    def verify_code(self, verify_type):
        code = str(random.randint(1000, 9999))
        CodeVerification.objects.create(
            # 57 qator shu joyi togirlandi oldin (user_id)
            user=self,
            verify_type=verify_type,
            code=code,
        )
        return code

    def check_username(self):
        if not self.username:
            temp_username = f"username{str(uuid.uuid4()).split('-')[-1]}"
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"{temp_username}{random.randint(0, 9)}"
            self.username = temp_username

    def check_pass(self):
        if not self.password:
            temp_pass = f"pass{str(uuid.uuid4()).split('-')[0]}"
            self.password = temp_pass

    def hashing_pass(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def check_email(self):
        if self.email:
            normalize_email = self.email.lower()
            self.email = normalize_email

    def token(self):
        refresh = RefreshToken.for_user(self)
        data = {
            'access': str(refresh.access_token),
            'refresh_token': str(refresh)
        }
        return data

    def save(self, *args, **kwargs):
        self.clean()
        return super(User, self).save(*args, **kwargs)

    def clean(self):
        self.check_email()
        self.check_username()
        self.check_pass()
        self.hashing_pass()


class CodeVerification(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )

    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=30, choices=VERIFY_TYPE)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verify_codes')
    expiration_time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_EMAIL)
        else:
            self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_PHONE)
        super(CodeVerification, self).save(*args, **kwargs)
