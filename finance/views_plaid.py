from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings

from .plaid_client import get_plaid_client
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_transactions import LinkTokenTransactions
from plaid.model.link_token_account_filters import LinkTokenAccountFilters
from plaid.model.depository_filter import DepositoryFilter
from plaid.model.depository_account_subtypes import DepositoryAccountSubtypes
from plaid.model.depository_account_subtype import DepositoryAccountSubtype
from plaid.model.credit_filter import CreditFilter
from plaid.model.credit_account_subtypes import CreditAccountSubtypes
from plaid.model.credit_account_subtype import CreditAccountSubtype

from django.db import transaction
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .plaid_client import get_plaid_client
from .models import Account

# Plaid imports
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest

from .views_webhook import _kick_off_transactions_sync


class CreatePlaidLinkTokenView(APIView):
    """
    POST /api/plaid/link-token/
    Body (optional): {"phone_number": "+1 415 5550123"}
    Response: {"link_token": "...", "expiration": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = get_plaid_client()

        phone_number = self.request.user.username  # optional
        client_user_id = str(self.request.user.id)

        qs = Account.objects.filter(user=self.request.user).exclude(plaid_access_token__isnull=True).exclude(plaid_access_token="")
        already_linked = qs.exists()
        linked_accounts = qs.count()

        access_token_for_update = None
        if already_linked:
            access_token_for_update = qs.values_list("plaid_access_token", flat=True).first()

        # Build the request user object
        user = LinkTokenCreateRequestUser(
            client_user_id=client_user_id,
        )

        # Products: transactions
        products = [Products("transactions")]

        # Transactions options
        tx_opts = LinkTokenTransactions(days_requested=730)

        # Account filters (checking + savings for depository, credit card for credit)
        filters = LinkTokenAccountFilters(
            depository=DepositoryFilter(
                account_subtypes=DepositoryAccountSubtypes([
                    DepositoryAccountSubtype("checking"),
                    DepositoryAccountSubtype("savings"),
                ])
            ),
            credit=CreditFilter(
                account_subtypes=CreditAccountSubtypes([
                    CreditAccountSubtype("credit card"),
                ])
            )
        )

        if access_token_for_update:
            req = LinkTokenCreateRequest(
                user=user,
                client_name="Personal Finance App",
                products=products,
                transactions=tx_opts,
                country_codes=[CountryCode("US")],
                language="en",
                account_filters=filters,
                access_token=access_token_for_update,
            )
            resolved_mode = "update"
        else:
            req = LinkTokenCreateRequest(
                user=user,
                client_name="Personal Finance App",
                products=products,
                transactions=tx_opts,
                country_codes=[CountryCode("US")],
                language="en",
                account_filters=filters,
            )
            resolved_mode = "add"

        try:
            res = client.link_token_create(req)
            data = res.to_dict() if hasattr(res, "to_dict") else dict(res)
            return Response(
                {
                    "link_token": data.get("link_token"),
                    "expiration": data.get("expiration"),
                    "already_linked": already_linked,
                    "linked_accounts": linked_accounts,
                    "mode": resolved_mode,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            # Bubble Plaid error details if available
            msg = getattr(e, "body", None) or str(e)
            return Response({"detail": f"Plaid error: {msg}"}, status=status.HTTP_400_BAD_REQUEST)

def _map_plaid_type_subtype(plaid_type: str, plaid_subtype: str):
    """
    Map Plaid types/subtypes to your accountType / subAccountType naming.
    """
    t = (plaid_type or "").lower()
    st = (plaid_subtype or "").lower()

    if t == "depository":
        if st == "checking":
            return ("checking", "DEMAND_DEPOSIT")
        if st == "savings":
            return ("savings", "SAVINGS")
        return ("depository", st or None)
    if t == "credit":
        if st in ("credit card", "credit_card", "credit"):
            return ("credit card", "CREDIT_CARD")
        return ("credit", st or None)
    if t == "loan":
        return ("loan", st or None)
    if t == "investment":
        return ("investments", st or None)
    # Fallback
    return (t or "current", st or None)

class ExchangePublicTokenView(APIView):
    """
    POST /api/plaid/exchange-public-token/
    Body: {"public_token": "...", "institution_name": "Optional bank name"}

    - Exchanges a Plaid public_token for an access_token
    - Fetches accounts via Plaid /accounts/get
    - Upserts rows into your finance_account table for the current user
    - Stores public_token (per requirement) and access_token/item_id
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        public_token = request.data.get("public_token")
        institution_name = request.data.get("institution_name")  # optional

        if not public_token:
            return Response({"detail": "public_token is required"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_plaid_client()

        # 1) Exchange public_token -> access_token, item_id
        try:
            exch_req = ItemPublicTokenExchangeRequest(public_token=public_token)
            exch_res = client.item_public_token_exchange(exch_req)
            exch = exch_res.to_dict()
            access_token = exch.get("access_token")
            item_id = exch.get("item_id")
            if not access_token or not item_id:
                return Response({"detail": "Failed to exchange token"}, status=400)
        except Exception as e:
            msg = getattr(e, "body", None) or str(e)
            return Response({"detail": f"Plaid exchange error: {msg}"}, status=400)

        # 2) Get accounts for this item
        try:
            acc_req = AccountsGetRequest(access_token=access_token)
            acc_res = client.accounts_get(acc_req)
            acc_data = acc_res.to_dict()
            plaid_accounts = acc_data.get("accounts", []) or []
        except Exception as e:
            msg = getattr(e, "body", None) or str(e)
            return Response({"detail": f"Plaid accounts error: {msg}"}, status=400)

        # 3) Upsert each account for this user
        imported = []
        for a in plaid_accounts:
            acct_id = a.get("account_id")
            name = a.get("name") or ""
            official_name = a.get("official_name") or ""
            mask = a.get("mask") or ""
            t = a.get("type")
            st = a.get("subtype")
            balances = a.get("balances") or {}

            accountType, subAccountType = _map_plaid_type_subtype(t, st)

            # Most reliable balances:
            current = balances.get("current")
            available = balances.get("available")
            iso_code = balances.get("iso_currency_code") or balances.get("unofficial_currency_code")

            # Mask as ****1234 if present
            masked_number = f"****{mask}" if mask else None

            # Account upsert key: (user, external account_id)
            obj, created = Account.objects.get_or_create(
                user=user,
                accountId=acct_id,
                defaults=dict(
                    isInternalAccount=False,
                    accountName=name or official_name or "Linked account",
                    officialAccountName=official_name or name,
                    accountType=accountType,
                    subAccountType=subAccountType,
                    accountNumber=masked_number,
                    currentBalance=current,
                    availableBalance=available,
                    isoCurrencyCode=iso_code,
                    public_token=public_token,              # per requirement
                    plaid_access_token=access_token,
                    plaid_item_id=item_id,
                    institution_name=institution_name,
                    mask=mask or None,
                    updatedDate=now(),
                ),
            )

            if not created:
                # Update fields on re-link / re-import
                obj.isInternalAccount = False
                obj.accountName = name or obj.accountName
                obj.officialAccountName = official_name or obj.officialAccountName
                obj.accountType = accountType
                obj.subAccountType = subAccountType
                obj.accountNumber = masked_number or obj.accountNumber
                obj.currentBalance = current if current is not None else obj.currentBalance
                obj.availableBalance = available if available is not None else obj.availableBalance
                obj.isoCurrencyCode = iso_code or obj.isoCurrencyCode
                obj.public_token = public_token  # (optional) keep last seen
                obj.plaid_access_token = access_token
                obj.plaid_item_id = item_id
                obj.institution_name = institution_name or obj.institution_name
                obj.mask = mask or obj.mask
                obj.updatedDate = now()
                obj.save(update_fields=[
                    "isInternalAccount","accountName","officialAccountName","accountType","subAccountType",
                    "accountNumber","currentBalance","availableBalance","isoCurrencyCode",
                    "public_token","plaid_access_token","plaid_item_id","institution_name","mask","updatedDate"
                ])

            imported.append({
                "id": obj.id,
                "accountId": obj.accountId,
                "accountName": obj.accountName,
                "accountType": obj.accountType,
                "subAccountType": obj.subAccountType,
                "accountNumber": obj.accountNumber,
                "currentBalance": obj.currentBalance,
                "availableBalance": obj.availableBalance,
                "isoCurrencyCode": obj.isoCurrencyCode,
                "institution_name": obj.institution_name,
                "created": created,
            })

        # (Optional) Since public_token is one-time, you can clear it after success:
        # Account.objects.filter(user=user, plaid_item_id=item_id).update(public_token=None)

        return Response({
            "item_id": item_id,
            "imported_count": len(imported),
            "accounts": imported,
        }, status=200)


class ManualSyncView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"detail": "item_id required"}, status=400)
        _kick_off_transactions_sync(item_id)
        return Response({"ok": True})