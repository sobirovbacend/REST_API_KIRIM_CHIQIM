from django.urls import path, include
from configapp.views import *
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()


urlpatterns = [
    # =====================
    # AUTH
    # =====================
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/verify-code/', VerifyCode.as_view(), name='verify-code'),
    path('auth/new-code/', NewCodeVerify.as_view(), name='new-code'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('user/update/ChangeUserInfo/', ChangeUserInfoView.as_view(), name='user-update'),
    path('user/photo/', UserPhotoView.as_view(), name='user-photo'),
    path('hisoblar/', AccountAPIView.as_view(), name='accounts'),
    path('Kirimlar/', IncomeAPIView.as_view(), name='incomes'),
    path('Chiqimlar/', ExpenseAPIView.as_view(), name='expenses'),
    path('hisobotlar/', ReportAPIView.as_view(), name='report'),
]
