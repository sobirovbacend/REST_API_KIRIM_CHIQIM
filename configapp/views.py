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
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
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

        verify.confirmed = True

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True
