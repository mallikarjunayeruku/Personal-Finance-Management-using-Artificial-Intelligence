
from rest_framework import serializers
from . import models

class OwnedSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BillsSerializer(OwnedSerializer):
    class Meta:
        model = models.Bills
        fields = '__all__'
class PaidMonthsSerializer(OwnedSerializer):
    class Meta:
        model = models.PaidMonths
        fields = '__all__'
class RecursiveTransactionsSerializer(OwnedSerializer):
    class Meta: model = models.RecursiveTransactions; fields = '__all__'
class TransactionsSerializer(OwnedSerializer):
    class Meta: model = models.Transactions; fields = '__all__'
class GoalSerializer(OwnedSerializer):
    class Meta: model = models.Goal; fields = '__all__'
class AchievedSerializer(OwnedSerializer):
    class Meta: model = models.Achieved; fields = '__all__'
class BudgetSerializer(OwnedSerializer):
    class Meta: model = models.Budget; fields = '__all__'
class AccountSerializer(OwnedSerializer):
    class Meta:
        model = models.Account
        fields = '__all__'
        read_only_fields = ("user",)

class AccountBalancesSerializer(OwnedSerializer):
    class Meta: model = models.AccountBalances; fields = '__all__'
class BalancesSerializer(OwnedSerializer):
    class Meta: model = models.Balances; fields = '__all__'
class AssetSerializer(OwnedSerializer):
    class Meta: model = models.Asset; fields = '__all__'
class PremiumSerializer(OwnedSerializer):
    class Meta: model = models.Premium; fields = '__all__'
class DevicesSerializer(OwnedSerializer):
    class Meta: model = models.Devices; fields = '__all__'
class LoginInformationSerializer(OwnedSerializer):
    class Meta: model = models.LoginInformation; fields = '__all__'
class FeedBackSerializer(OwnedSerializer):
    class Meta: model = models.FeedBack; fields = '__all__'
