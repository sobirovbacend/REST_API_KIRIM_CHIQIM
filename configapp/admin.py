from django.contrib import admin
from .models import Income, Expense, Account
from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Income)
admin.site.register(Expense)
