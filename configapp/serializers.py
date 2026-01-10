from subprocess import check_output

from .models import *
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from baseapp.utility import *
from baseapp.email import *
from django.contrib.auth.password_validation import validate_password



class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True, required=False)
    suth_status = serializers.CharField(read_only=True, required=False)
    email_phone_number = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['validate_email_phone_number'] = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'auth_type',
            'suth_status',
            'id',
            'email_phone_number',
        ]

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.verify_code(VIA_EMAIL)
            send_email_code(user.email, code)
            print(code)
        elif user.auth_type == VIA_PHONE:
            code = user.verify_code(VIA_PHONE)
            print(code)

            pass
        else:
            data = {
                'success': 'False',
                'message': 'Telefon raqam yoki email togri kiriting'
            }
            raise ValidationError(data)
        user.save()
        return user

    def validate(self, data):
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = data.get('email_phone_number')
        user_input_type = email_or_phone(user_input)

        if user_input_type == 'email':
            data = {
                'auth_type': VIA_EMAIL,
                'email': user_input
            }
        elif user_input_type == 'phone':
            data = {
                'auth_type': VIA_PHONE,
                'phone_number': user_input
            }
        else:

            data = {
                'success': 'False',
                'message': 'Telefon raqam yoki email kiriting'
            }
            raise ValidationError(data)

        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            raise ValidationError("Bu email allaqachon mavjud")
        elif value and User.objects.filter(phone_number=value).exists():
            raise ValidationError('Bu telefon raqam allaqchon mavjud')
        return value

    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError({
                'success': False,
                'message': 'Parollar mos emas'
            })

        if password:
            validate_password(password)

        return data

    # boshqa validate metodlari o‘rnida qoladi

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.first_name = validated_data.get('first_name', instance.first_name)

        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)

        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE

        instance.save()
        return instance


class UserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField()
    def update(self, instance, validated_data):
        photo = validated_data.get('photo',None)
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE

        instance.save()
        return instance





class LoginSerializer(serializers.Serializer):
    email_phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        login_input = data.get('email_phone_number')
        password = data.get('password')

        if not login_input or not password:
            raise ValidationError({
                'success': False,
                'message': 'Email/telefon va parol majburiy'
            })

        input_type = email_or_phone(login_input)

        if not input_type:
            raise ValidationError({
                'success': False,
                'message': 'Email yoki telefon noto‘g‘ri formatda'
            })

        # =========================
        # USERNI TOPISH
        # =========================
        if input_type == 'email':
            user = User.objects.filter(email=login_input.lower()).first()
        else:
            phone = normalize_phone(login_input)
            user = User.objects.filter(phone_number=phone).first()

        if not user:
            raise ValidationError({
                'success': False,
                'message': 'Foydalanuvchi topilmadi'
            })

        # =========================
        # AUTH STATUS TEKSHIRISH
        # =========================
        if user.auth_status not in [DONE, PHOTO_DONE]:
            raise ValidationError({
                'success': False,
                'message': 'Ro‘yxatdan o‘tish yakunlanmagan'
            })

        # =========================
        # PAROL TEKSHIRISH
        # =========================
        if not user.check_password(password):
            raise ValidationError({
                'success': False,
                'message': 'Parol noto‘g‘ri'
            })

        data['user'] = user
        return data



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()






