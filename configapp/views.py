from pyexpat.errors import messages
from rest_framework.parsers import MultiPartParser, FormParser

from django.shortcuts import render, get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from rest_framework.views import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets, permissions
import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.views import *
from datetime import datetime


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]


class VerifyCode(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=VerifyCodeSerializer)
    def post(self, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify_code(user, code)
        data = {
            'success': True,
            'auth_status': user.auth_status,
            'access_token': user.token()['access'],
            'refresh': user.token()['refresh_token']
        }

        return Response(data)

    @staticmethod
    def check_verify_code(user, code):
        verify = user.verify_codes.filter(code=code, confirmed=False, expiration_time__gte=datetime.now())
        if not verify.exists():
            data = {
                'success': False,
                'message': 'Kod eskirgan yoki xato'
            }

            raise ValidationError(data)

        else:
            verify.update(confirmed=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True


class NewCodeVerify(APIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, *args, **kwargs):
        user = self.request.user
        self.chect_verify_code(user)
        if user.auth_type == VIA_EMAIL:
            code = user.verify_code(VIA_EMAIL)
            send_email_code(user.email, code)
            print(code)
        elif user.auth_type == VIA_PHONE:
            code = user.verify_code(VIA_EMAIL)
            print(code)

        data = {
            'success': True,
            'message': 'Yangi kod yuborildi'
        }

        return Response(data)

    @staticmethod
    def chect_verify_code(user):
        verify = user.verify_codes.filter(confirmed=False, expiration_time__gte=datetime.now())
        if verify.exists():
            data = {
                'success': False,
                'message': 'Sizda hali active code bor'
            }

            raise ValidationError(data)

        return True


class ChangeUserInfo(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = ChangeUserInfoSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        response.data = {
            'success': True,
            'message': 'Malumotlar yangilandi',
            'data': response.data
        }
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)

        response.data = {
            'success': True,
            'message': 'Malumotlar yangilandi',
            'data': response.data
        }
        return response


class UserPhotoView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)



    @swagger_auto_schema(
        request_body=UserPhotoSerializer,
        consumes=['multipart/form-data']
    )


    def put(self, request):
        serializer = UserPhotoSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'Sizning rasmingiz o‘zgartirildi'
        }, status=status.HTTP_200_OK)



class LoginView(APIView):
    permission_classes = (AllowAny,)


    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        return Response({
            'success': True,
            'message': 'Login muvaffaqiyatli',
            **user.token()
        })




class LogoutView(APIView):
    permission_classes = [IsAuthenticated]



    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # serverda refresh tokenni bekor qiladi
            return Response({"success": True, "message": "Logout muvaffaqiyatli"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"success": False, "message": "Token xato yoki topilmadi"}, status=status.HTTP_400_BAD_REQUEST)
