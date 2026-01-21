from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import UserManager

from rest_framework_simplejwt.tokens import RefreshToken

from baseapp.models import BaseModel

import uuid
import random
from datetime import timedelta, datetime

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

    user_role = models.CharField(
        max_length=30,
        choices=USER_ROLE,
        default=ORDINARY_USER
    )
    auth_status = models.CharField(
        max_length=30,
        choices=AUTH_STATUS,
        default=NEW
    )
    auth_type = models.CharField(
        max_length=30,
        choices=AUTH_TYPE
    )

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)

    photo = models.ImageField(
        upload_to='user_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'png', 'jpeg']
        )]
    )

    def __str__(self):
        return self.username

    # ------------------------
    # BUSINESS LOGIC
    # ------------------------

    def check_username(self):
        if not self.username:
            temp_username = f"user_{uuid.uuid4().hex[:8]}"
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"user_{uuid.uuid4().hex[:8]}"
            self.username = temp_username

    def check_email(self):
        if self.email:
            self.email = self.email.lower()

    def check_pass(self):
        if not self.password:
            temp_pass = UserManager().make_random_password()
            self.password = temp_pass

    def hashing_password(self):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.set_password(self.password)

    def clean(self):
        self.check_email()
        self.check_username()
        self.hashing_password()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    # ------------------------
    # JWT TOKEN
    # ------------------------

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    # ------------------------
    # VERIFICATION
    # ------------------------

    def verify_code(self, verify_type):
        code = str(random.randint(1000, 9999))
        CodeVerification.objects.create(
            user=self,
            verify_type=verify_type,
            code=code
        )
        return code


class CodeVerification(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verify_codes'
    )
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=30, choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.code}"

    def save(self, *args, **kwargs):
        if not self.expiration_time:
            if self.verify_type == VIA_EMAIL:
                self.expiration_time = timezone.now() + timedelta(
                    minutes=settings.EXPIRATION_EMAIL
                )
            else:
                self.expiration_time = timezone.now() + timedelta(
                    minutes=settings.EXPIRATION_PHONE
                )
        super().save(*args, **kwargs)


class Account(models.Model):
    ACCOUNT_TYPE = (
        ('card', 'Karta'),
        ('cash', 'Naqd'),
    )

    CURRENCY = (
        ('UZS', 'UZS'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY)

    bank_name = models.CharField(max_length=100, blank=True, null=True)
    last_digits = models.CharField(max_length=4, blank=True, null=True)
    expire_date = models.CharField(max_length=5, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Income(models.Model):
    CURRENCY = (
        ('UZS', 'UZS'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    source = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.source} - {self.amount}"


class Expense(models.Model):
    CURRENCY = (
        ('UZS', 'UZS'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    )

    CATEGORY = (
        ('kommunal', 'Kommunal'),
        ('ovqat', 'Ovqat'),
        ('transport', 'Transport'),
        ('boshqa', 'Boshqa'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    category = models.CharField(max_length=30, choices=CATEGORY)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.category} - {self.amount}"



