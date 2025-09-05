
from rest_framework import viewsets, permissions
from django.db.models import QuerySet
from . import models, serializers
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
class TransactionsViewSet(BaseOwnedViewSet): queryset = models.Transactions.objects.select_related('account').all(); serializer_class = serializers.TransactionsSerializer; search_fields=('name','merchantName','category','currencyCode')
class GoalViewSet(BaseOwnedViewSet): queryset = models.Goal.objects.all(); serializer_class = serializers.GoalSerializer; search_fields=('goalName','goalType','goalCategory')
class AchievedViewSet(BaseOwnedViewSet): queryset = models.Achieved.objects.select_related('goal').all(); serializer_class = serializers.AchievedSerializer; search_fields=('owner_id',)
class BudgetViewSet(BaseOwnedViewSet): queryset = models.Budget.objects.all(); serializer_class = serializers.BudgetSerializer; search_fields=('title',)
class AccountViewSet(BaseOwnedViewSet): queryset = models.Account.objects.all(); serializer_class = serializers.AccountSerializer; search_fields=('accountName','officialAccountName','accountNumber','accountType')
class AccountBalancesViewSet(BaseOwnedViewSet): queryset = models.AccountBalances.objects.select_related('account').all(); serializer_class = serializers.AccountBalancesSerializer
class BalancesViewSet(BaseOwnedViewSet): queryset = models.Balances.objects.select_related('accountBalances').all(); serializer_class = serializers.BalancesSerializer
class AssetViewSet(BaseOwnedViewSet): queryset = models.Asset.objects.all(); serializer_class = serializers.AssetSerializer; search_fields=('name','location')
class PremiumViewSet(BaseOwnedViewSet): queryset = models.Premium.objects.all(); serializer_class = serializers.PremiumSerializer
class DevicesViewSet(BaseOwnedViewSet): queryset = models.Devices.objects.all(); serializer_class = serializers.DevicesSerializer; search_fields=('deviceName','model','brand')
class LoginInformationViewSet(BaseOwnedViewSet): queryset = models.LoginInformation.objects.select_related('devices').all(); serializer_class = serializers.LoginInformationSerializer
class FeedBackViewSet(BaseOwnedViewSet): queryset = models.FeedBack.objects.all(); serializer_class = serializers.FeedBackSerializer; search_fields=('package','user')
