from decimal import Decimal
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db import transaction
from .models import Account

def to_decimal(n) -> Decimal:
    if n is None:
        return Decimal("0")
    try:
        return Decimal(str(n))
    except Exception:
        return Decimal("0")

def delta_for(amount, is_income: bool) -> Decimal:
    amt = to_decimal(amount)
    return amt if is_income else (amt * Decimal("-1"))

@transaction.atomic
def apply_delta_to_account(account_id, delta: Decimal):
    # Coalesce to 0 to avoid None math
    Account.objects.select_for_update().filter(id=account_id).update(
        currentBalance=Coalesce(F("currentBalance"), Value(0)) + delta
    )
