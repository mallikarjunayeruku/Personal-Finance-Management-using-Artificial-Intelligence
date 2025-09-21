
from rest_framework import viewsets, permissions
from django.db.models import QuerySet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from . import models, serializers
from django.db import transaction as db_tx
from .models import Transactions, Category
from .serializers import TransactionsSerializer, CategorySerializer
from .services import delta_for, apply_delta_to_account

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'user_id', None) == request.user.id

class BaseOwnedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    search_fields = ('id',)
    ordering_fields = '__all__'
    filterset_fields = '__all__'
    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BillsViewSet(BaseOwnedViewSet): queryset = models.Bills.objects.all(); serializer_class = serializers.BillsSerializer; search_fields=('title','category')
class PaidMonthsViewSet(BaseOwnedViewSet): queryset = models.PaidMonths.objects.select_related('bills').all(); serializer_class = serializers.PaidMonthsSerializer; search_fields=('accountId',)
class RecursiveTransactionsViewSet(BaseOwnedViewSet): queryset = models.RecursiveTransactions.objects.all(); serializer_class = serializers.RecursiveTransactionsSerializer; search_fields=('tableName',)
class TransactionsViewSet(BaseOwnedViewSet):
    queryset = models.Transactions.objects.select_related('account').all()
    serializer_class = TransactionsSerializer
    search_fields=('name','merchantName','category','currencyCode')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_destroy(self, instance: Transactions):
        # deleting a tx should undo its effect
        with db_tx.atomic():
            d = delta_for(instance.amount, instance.isIncome)
            apply_delta_to_account(instance.account_id, -d)
            super().perform_destroy(instance)

class GoalViewSet(BaseOwnedViewSet): queryset = models.Goal.objects.all(); serializer_class = serializers.GoalSerializer; search_fields=('goalName','goalType','goalCategory')
class AchievedViewSet(BaseOwnedViewSet): queryset = models.Achieved.objects.select_related('goal').all(); serializer_class = serializers.AchievedSerializer; search_fields=('owner_id',)
class BudgetViewSet(BaseOwnedViewSet): queryset = models.Budget.objects.all(); serializer_class = serializers.BudgetSerializer; search_fields=('title',)
class AccountViewSet(BaseOwnedViewSet):
    queryset = models.Account.objects.all()
    serializer_class = serializers.AccountSerializer
    search_fields=('accountName','officialAccountName','accountNumber','accountType')
    ordering = ("accountName", "id")
    ordering_fields = ("accountName", "updatedDate", "createdDate", "id")

class AccountBalancesViewSet(BaseOwnedViewSet): queryset = models.AccountBalances.objects.select_related('account').all(); serializer_class = serializers.AccountBalancesSerializer
class BalancesViewSet(BaseOwnedViewSet): queryset = models.Balances.objects.select_related('accountBalances').all(); serializer_class = serializers.BalancesSerializer
class AssetViewSet(BaseOwnedViewSet): queryset = models.Asset.objects.all(); serializer_class = serializers.AssetSerializer; search_fields=('name','location')
class PremiumViewSet(BaseOwnedViewSet): queryset = models.Premium.objects.all(); serializer_class = serializers.PremiumSerializer
class DevicesViewSet(BaseOwnedViewSet): queryset = models.Devices.objects.all(); serializer_class = serializers.DevicesSerializer; search_fields=('deviceName','model','brand')
class LoginInformationViewSet(BaseOwnedViewSet): queryset = models.LoginInformation.objects.select_related('devices').all(); serializer_class = serializers.LoginInformationSerializer
class FeedBackViewSet(BaseOwnedViewSet): queryset = models.FeedBack.objects.all(); serializer_class = serializers.FeedBackSerializer; search_fields=('package','user')


class CategoryPagination(PageNumberPagination):
    page_size = 100  # default page size
    max_page_size = 1000  # allow clients to override up to this via ?page_size=

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ("name", "slug")
    ordering = ("name",)
    pagination_class = CategoryPagination

