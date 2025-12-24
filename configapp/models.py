import random
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

from baseapp.models import BaseModel
from config.settings import AUTH_USER_MODEL,EXPIRATION_PHONE,EXPIRATION_EMAIL

ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user','manager','admin')
NEW, CODE_VERIFIED, DONE, PHOTO_DONE = ('new','code_verified','done','photo_done')
VIA_EMAIL, VIA_PHONE = ('via_email','via_phone')




class User(AbstractUser,BaseModel):
    USER_ROLE = (
        (ORDINARY_USER,ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )

    AUTH_STATUS = (
    (NEW,NEW),
    (CODE_VERIFIED,CODE_VERIFIED),
    (DONE,DONE),
    (PHOTO_DONE,PHOTO_DONE)
    )

    AUTH_TYPE = (
    (VIA_EMAIL,VIA_EMAIL),
    (VIA_PHONE,VIA_PHONE)
    )

    user_role = models.CharField(max_length=30, choices=USER_ROLE,default=ORDINARY_USER)
    auth_status = models.CharField(max_length=30, choices=AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=30, choices=AUTH_TYPE)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    photo = models.ImageField(upload_to='user-photo',blank=True,null=True, \
                              validators=[FileExtensionValidator(allowed_extensions=['.png','jpg','jpeg','heic'])])


    def __str__(self):
        return self.username


    def verify_code(self,verify_type):
        code = str(random.randint(1000,9999))
        CodeVerification.objects.create(
            user_id=self.id,
            verify_type=verify_type,
            code = code
        )
        return code



class CodeVerification(BaseModel):
    VERIFY_TYPE = (
    (VIA_EMAIL,VIA_EMAIL),
    (VIA_PHONE,VIA_PHONE)
    )
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=30,choices=VERIFY_TYPE)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    expiration_time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)


    def __str__(self):
        return str(self.user.__str__())



    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_EMAIL)

        else:
            self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_PHONE)

        super(CodeVerification,self).save(*args, **kwargs)