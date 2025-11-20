from decimal import Decimal
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db import transaction

from . import plaid_client
from .models import Account, Category
from typing import Dict, Optional

from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import Account, Transactions
from .plaid_client import get_plaid_client
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.api_client import ApiException


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


def _get_cursor(item_id: str) -> Optional[str]:
    """Retrieve stored Plaid cursor from Account."""
    return (
        Account.objects
        .filter(plaid_item_id=item_id)
        .values_list("plaid_transactions_cursor", flat=True)
        .first()
    )


def _set_cursor(item_id: str, cursor: Optional[str]) -> None:
    """Save the next Plaid cursor for this item."""
    Account.objects.filter(plaid_item_id=item_id).update(plaid_transactions_cursor=cursor)


def _build_account_map_for_item(item_id: str) -> Dict[str, Account]:
    """Map Plaid 'account_id' → local Account using Accounts.accountId."""
    accs = Account.objects.filter(plaid_item_id=item_id).only("id", "accountId", "plaid_item_id")
    return {a.accountId: a for a in accs}

def _resolve_category_id_from_pfc_detailed(detailed: Optional[str]) -> Optional[int]:
    if not detailed:
        return  Category.objects.filter(description__iexact="UNKNOWN").only("id").first()
    obj = Category.objects.filter(description__iexact=detailed).only("id").first()
    if obj:
        return obj.id
    return Category.objects.filter(description__iexact="UNKNOWN").only("id").first()

def _map_defaults_from_plaid(tx: dict, account_obj: Account, user_id: int) -> dict:
    """
    Convert Plaid transaction -> finance_transactions schema.
    Adjusts field names and types to your table definition.
    """
    loc = tx.get("location") or {}
    pfc = tx.get("personal_finance_category") or {}
    detailed = pfc.get("detailed")  # e.g., 'GENERAL_MERCHANDISE_SUPERSTORES'
    category_id = _resolve_category_id_from_pfc_detailed(detailed)

    return {
        # Foreign keys
        "account_id": account_obj.id,
        "user_id": account_obj.user_id,  # assuming Account FK to user

        # Core transaction fields
        "amount": tx.get("amount"),
        "name": tx.get("name"),
        "merchantName": tx.get("merchant_name"),
        "currencyCode": tx.get("iso_currency_code"),
        "checkNumber": tx.get("check_number"),
        "note": None,  # Plaid doesn't provide notes

        # Timestamps
        "createdDate": tx.get("authorized_datetime") or tx.get("authorized_date"),
        "transactionDate": tx.get("datetime") or tx.get("date"),

        # Location
        "location": ", ".join(
            filter(None, [loc.get("address"), loc.get("city"), loc.get("region")])
        ) or None,
        "latitude": loc.get("lat"),
        "longitude": loc.get("lon"),

        # Derived / flags
        "isIncome": tx.get("amount", 0) < 0,  # treat negatives as income if needed
        "isCashAccount": False,
        "canDelete": False,
        "repeat": None,
        "path": tx.get("personal_finance_category_icon_url") or tx.get("logo_url"),

        # Audit fields
        "created_at": timezone.now(),
        "category_id": category_id,  # <-- FK set here
    }


def sync_plaid_item_transactions(item_id: str) -> dict:
    """
    Full Plaid → finance_transactions sync loop.
    Stores cursor in Account.plaid_transactions_cursor.
    """
    any_acc = (
        Account.objects
        .filter(plaid_item_id=item_id)
        .select_related("user")
        .first()
    )
    if not any_acc or not any_acc.plaid_access_token:
        raise ObjectDoesNotExist(f"No account with item_id={item_id} having a Plaid access token.")

    access_token = any_acc.plaid_access_token
    cursor = _get_cursor(item_id)
    acct_map = _build_account_map_for_item(item_id)

    added_total = modified_total = removed_total = 0
    has_more = True

    try:
        while has_more:
            req_kwargs = {"access_token": access_token , "count": 500}
            if cursor:
                req_kwargs["cursor"] = cursor
            req = TransactionsSyncRequest(**req_kwargs)
            resp = get_plaid_client().transactions_sync(req)

            added = resp["added"]
            modified = resp["modified"]
            removed = resp["removed"]

            with db_transaction.atomic():
                for tx in list(added) + list(modified):
                    plaid_txn_id = tx["transaction_id"]
                    tx_acc = acct_map.get(tx.get("account_id"), any_acc)
                    defaults = _map_defaults_from_plaid(tx, tx_acc, any_acc.user_id)

                    Transactions.objects.update_or_create(
                        id=plaid_txn_id,
                        defaults=defaults,
                    )

                for tx in removed:
                    plaid_txn_id = tx.get("transaction_id") if isinstance(tx, dict) else tx
                    Transactions.objects.filter(id=plaid_txn_id).update(canDelete=False)

            added_total += len(added)
            modified_total += len(modified)
            removed_total += len(removed)

            has_more = resp["has_more"]
            cursor = resp["next_cursor"]

        _set_cursor(item_id, cursor)

    except ApiException as e:
        # Log or raise
        raise

    return {
        "item_id": item_id,
        "added": added_total,
        "modified": modified_total,
        "removed": removed_total,
        "next_cursor": cursor,
        "synced_at": timezone.now(),
    }
