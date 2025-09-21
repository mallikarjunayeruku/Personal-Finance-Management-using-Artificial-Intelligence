
from rest_framework import serializers
from . import models
from django.db import transaction as db_tx
from .models import Transactions, Category
from .services import delta_for, apply_delta_to_account


class OwnedSerializer(serializers.ModelSerializer):
    def create(self, validated):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated["user"] = request.user           # << user, not owner
            validated["ownerId"] = str(request.user.id)  # if you still keep that field
        return super().create(validated)

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

class TransactionsSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    categoryName = serializers.CharField(write_only=True, required=False, allow_blank=True)
    category_display = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transactions
        fields = (
            "id", "amount", "name", "merchantName", "currencyCode", "checkNumber",
            "note", "createdDate", "transactionDate", "location", "latitude",
            "longitude", "path", "isIncome", "repeat", "account", "isCashAccount",
            "canDelete",
            "category",           # FK id
            "category_display",   # read-only name for UI
            "categoryName",       # optional write-only to create/resolve by name
        )
        read_only_fields = ("user","ownerId")

    def validate(self, attrs):
        cat_name = attrs.pop("categoryName", "").strip() if "categoryName" in attrs else ""
        if cat_name and not attrs.get("category"):
            cat, _ = Category.objects.get_or_create(name=cat_name[:80])
            attrs["category"] = cat
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and hasattr(self.instance, "user") is False:
            # if you use an OwnedSerializer base, you may already set owner; otherwise:
            validated_data["user"] = request.user
            validated_data["user_id"] = str(request.user.id)

        with db_tx.atomic():
            obj = super().create(validated_data)
            # +amount for income, -amount for expense
            d = delta_for(obj.amount, obj.isIncome)
            apply_delta_to_account(obj.account_id, d)
            return obj

    def update(self, instance, validated_data):
        old_account_id = instance.account_id
        old_delta = delta_for(instance.amount, instance.isIncome)

        # new values (default to old if not provided)
        new_amount = validated_data.get("amount", instance.amount)
        new_is_income = validated_data.get("isIncome", instance.isIncome)
        new_account = validated_data.get("account", instance.account)
        new_account_id = getattr(new_account, "id", None) or instance.account_id
        new_delta = delta_for(new_amount, new_is_income)

        with db_tx.atomic():
            obj = super().update(instance, validated_data)

            # Reverse old effect, then apply new effect.
            if old_account_id == new_account_id:
                net = new_delta - old_delta
                if net:
                    apply_delta_to_account(new_account_id, net)
            else:
                # moved to a different account:
                if old_delta:
                    apply_delta_to_account(old_account_id, -old_delta)
                if new_delta:
                    apply_delta_to_account(new_account_id, new_delta)

            return obj

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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")

