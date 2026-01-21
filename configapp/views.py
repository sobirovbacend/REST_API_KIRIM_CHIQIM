from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from .serializers import *
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]



class VerifyCode(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=VerifyCodeSerializer)
    def post(self, request):
        user = request.user
        code = request.data.get('code')

        self.check_verify_code(user, code)

        return Response({
            'success': True,
            'auth_status': user.auth_status,
            **user.token()
        })

    @staticmethod
    def check_verify_code(user, code):
        verify = user.verify_codes.filter(
            code=code,
            confirmed=False,
            expiration_time__gte=timezone.now()
        )

        if not verify.exists():
            raise ValidationError("Kod eskirgan yoki xato")

        verify.update(confirmed=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()


class NewCodeVerify(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        self.check_active_code(user)

        if user.auth_type == VIA_EMAIL:
            code = user.verify_code(VIA_EMAIL)
            send_email_code(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.verify_code(VIA_PHONE)
            print(f"SMS CODE: {code}")

        return Response({
            'success': True,
            'message': 'Yangi kod yuborildi'
        })

    @staticmethod
    def check_active_code(user):
        if user.verify_codes.filter(
            confirmed=False,
            expiration_time__gte=timezone.now()
        ).exists():
            raise ValidationError("Sizda hali aktiv kod mavjud")



from drf_yasg.utils import swagger_auto_schema

class ChangeUserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=ChangeUserInfoSerializer)
    def put(self, request):
        serializer = ChangeUserInfoSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'message': 'Maʼlumotlar yangilandi'})

    @swagger_auto_schema(request_body=ChangeUserInfoSerializer)
    def patch(self, request):
        return self.put(request)




class UserPhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
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
            'message': 'Rasm yangilandi'
        })



class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        return Response({
            'success': True,
            **user.token()
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token yuborilmadi"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "success": True,
                    "message": "Tizimdan muvaffaqiyatli chiqildi"
                },
                status=status.HTTP_200_OK
            )

        except TokenError:
            # Token allaqachon blacklist qilingan yoki yaroqsiz
            return Response(
                {
                    "success": True,
                    "message": "Siz allaqachon tizimdan chiqqansiz"
                },
                status=status.HTTP_200_OK
            )

        except Exception:
            # HAR QANDAY kutilmagan xato
            return Response(
                {
                    "success": False,
                    "message": "Xatolik yuz berdi, qayta urinib ko‘ring"
                },
                status=status.HTTP_400_BAD_REQUEST
            )



from decimal import Decimal

def convert_currency(amount, from_currency, to_currency):
    rates = {
        "UZS": Decimal('1'),
        "USD": Decimal('12051.71'),  # 1 USD ≈ 12 051.71 UZS
        "EUR": Decimal('13500'),  # agar kerak bo'lsa taxminiy EUR kursi
    }

    # Avval UZS ga o'tkazamiz
    amount_in_uzs = Decimal(amount) * rates.get(from_currency, Decimal('1'))
    # Keyin kerakli valyutaga
    converted_amount = amount_in_uzs / rates.get(to_currency, Decimal('1'))
    return converted_amount.quantize(Decimal('0.01'))

class IncomeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        incomes = Income.objects.filter(user=request.user).order_by('-created_at')
        serializer = IncomeSerializer(incomes, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=IncomeSerializer)
    def post(self, request):
        serializer = IncomeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data['account']
        amount = serializer.validated_data['amount']
        currency = serializer.validated_data['currency']

        # Valyuta farqi bo‘lsa, konvertatsiya qilamiz
        if currency != account.currency:
            amount_to_add = convert_currency(amount, currency, account.currency)
        else:
            amount_to_add = Decimal(amount)

        # Hisob balansini yangilash
        account.balance = Decimal(account.balance) + amount_to_add
        account.save()

        # Kirimni saqlash
        income = serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ExpenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expenses = Expense.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ExpenseSerializer)
    def post(self, request):
        serializer = ExpenseSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data['account']
        amount = serializer.validated_data['amount']

        if account.balance < amount:
            raise ValidationError({
                'message': 'Hisobda mablag‘ yetarli emas'
            })

        account.balance -= amount
        account.save()

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = Account.objects.filter(user=request.user)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)
    @swagger_auto_schema(request_body=AccountSerializer)
    def post(self, request):
        serializer = AccountSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'all')

        incomes = Income.objects.filter(user=user)
        expenses = Expense.objects.filter(user=user)

        now = timezone.now()

        if period == 'daily':
            incomes = incomes.filter(created_at__date=now.date())
            expenses = expenses.filter(created_at__date=now.date())

        elif period == 'monthly':
            incomes = incomes.filter(
                created_at__year=now.year,
                created_at__month=now.month
            )
            expenses = expenses.filter(
                created_at__year=now.year,
                created_at__month=now.month
            )

        elif period == 'yearly':
            incomes = incomes.filter(created_at__year=now.year)
            expenses = expenses.filter(created_at__year=now.year)

        total_income = incomes.aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_expense = expenses.aggregate(
            total=Sum('amount')
        )['total'] or 0

        return Response({
            'period': period,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense
        })



