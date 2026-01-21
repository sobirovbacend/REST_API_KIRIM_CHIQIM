from subprocess import check_output

from .models import *
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from baseapp.utility import *
from baseapp.email import *
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from baseapp.email import send_email_code
from baseapp.utility import email_or_phone

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    email_phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status',
            'email_phone_number',
        )
        read_only_fields = ('id', 'auth_type', 'auth_status')

    def validate_email_phone_number(self, value):
        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise ValidationError("Bu email allaqachon mavjud")

        if User.objects.filter(phone_number=value).exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud")

        return value

    def validate(self, attrs):
        user_input = attrs.get('email_phone_number')
        input_type = email_or_phone(user_input)

        if input_type == 'email':
            attrs['email'] = user_input.lower()
            attrs['auth_type'] = 'email'

        elif input_type == 'phone':
            attrs['phone_number'] = normalize_phone(user_input)
            attrs['auth_type'] = 'phone'

        else:
            raise ValidationError("Email yoki telefon raqam kiriting")

        return attrs

    def create(self, validated_data):
        validated_data.pop('email_phone_number')

        user = User.objects.create(**validated_data)

        if user.auth_type == 'email':
            code = user.verify_code('email')
            send_email_code(user.email, code)

        elif user.auth_type == 'phone':
            code = user.verify_code('phone')
            print(f"SMS code: {code}")

        user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.token())
        return data


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    username = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Bu username allaqachon mavjud")]
    )
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Parollar mos emas")
        validate_password(attrs['password'])
        return attrs

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        new_username = validated_data.get('username')
        if new_username and new_username != instance.username:
            instance.username = new_username

        instance.set_password(validated_data['password'])

        if getattr(instance, 'auth_status', None) == CODE_VERIFIED:
            instance.auth_status = DONE

        instance.save()
        return instance


class UserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField()

    def update(self, instance, validated_data):
        instance.photo = validated_data['photo']
        instance.auth_status = PHOTO_DONE
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email_phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_input = attrs.get('email_phone_number')
        password = attrs.get('password')

        input_type = email_or_phone(login_input)
        if not input_type:
            raise ValidationError("Email yoki telefon noto‘g‘ri")

        if input_type == 'email':
            user = User.objects.filter(email=login_input.lower()).first()
        else:
            user = User.objects.filter(
                phone_number=normalize_phone(login_input)
            ).first()

        if not user:
            raise ValidationError("Foydalanuvchi topilmadi")

        if user.auth_status not in (DONE, PHOTO_DONE):
            raise ValidationError("Ro‘yxatdan o‘tish yakunlanmagan")

        if not user.check_password(password):
            raise ValidationError("Parol noto'g'ri")

        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# Hisoblar
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('user', 'balance', 'created_at')


# kirimlar
class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

    def create(self, validated_data):
        # Faqat user ni qo‘shamiz
        validated_data['user'] = self.context['request'].user

        # Hisobni yangilashni serializerda qilmaymiz
        # Valyuta konvertatsiyasi va balance += views.py da bo‘ladi

        return super().create(validated_data)


# Expense - chiqimlar
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
