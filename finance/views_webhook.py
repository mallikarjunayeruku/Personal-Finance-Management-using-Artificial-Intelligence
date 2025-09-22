from django.conf import settings
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import PlaidWebhookEvent
from .models import Account


def _resolve_user_by_item_id(item_id: str):
    """
    Find the owning user given a Plaid item_id.
    Works with either PlaidItem (preferred) or legacy Account.plaid_item_id.
    """
    if not item_id:
        return None

    acc = Account.objects.filter(plaid_item_id=item_id).select_related("user").first()
    if acc:
        return acc.user

    return None

def _kick_off_transactions_sync(item_id: str):
    """
    Hook to trigger your background sync job (Celery/RQ) or a direct call.
    Keep the webhook fast: enqueue and return.
    """
    # Example (pseudo):
    # from .tasks import plaid_transactions_sync
    # plaid_transactions_sync.delay(item_id=item_id)
    pass


@method_decorator(csrf_exempt, name="dispatch")
class PlaidWebhookView(APIView):
    """
    Endpoint: POST /api/plaid/webhook/
    Unauthenticated (Plaid calls it) + optional lightweight secret check.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Optional shared-secret verification
        expected = getattr(settings, "PLAID_WEBHOOK_SHARED_SECRET", "") or ""
        provided = request.headers.get("X-Webhook-Secret", "")
        if expected and provided != expected:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data if isinstance(request.data, dict) else {}
        webhook_type = payload.get("webhook_type")
        webhook_code = payload.get("webhook_code")
        item_id = payload.get("item_id")
        environment = payload.get("environment")
        initial_done = bool(payload.get("initial_update_complete"))
        historical_done = bool(payload.get("historical_update_complete"))

        # Persist the event first (idempotent audit log)
        evt = PlaidWebhookEvent.objects.create(
            item_id=item_id,
            webhook_type=webhook_type,
            webhook_code=webhook_code,
            environment=environment,
            initial_update_complete=initial_done,
            historical_update_complete=historical_done,
            body=payload,
            status="received",
        )

        # Branch on type/code. Keep it FAST; do heavy work async.
        try:
            if webhook_type == "TRANSACTIONS":
                if webhook_code in ("SYNC_UPDATES_AVAILABLE", "DEFAULT_UPDATE", "HISTORICAL_UPDATE"):
                    # Find the user; optional but useful for routing
                    user = _resolve_user_by_item_id(item_id)
                    # Enqueue/trigger your transactions sync
                    _kick_off_transactions_sync(item_id)
                    evt.status = "done"
                elif webhook_code == "RECURRING_TRANSACTIONS_UPDATE":
                    # Optional: handle recurring updates separately
                    evt.status = "done"
                else:
                    # Unhandled code under TRANSACTIONS
                    evt.status = "done"

            elif webhook_type in ("ITEM", "AUTH", "LIABILITIES",
                                  "HOLDINGS", "INVESTMENTS_TRANSACTIONS", "ASSETS"):
                # You can add specialized handling here if needed
                evt.status = "done"
            else:
                # Unknown type — still 200 OK to acknowledge
                evt.status = "done"

            evt.processed_at = now()
            evt.save(update_fields=["status", "processed_at"])

        except Exception as e:
            evt.status = "error"
            evt.error = str(e)
            evt.processed_at = now()
            evt.save(update_fields=["status", "error", "processed_at"])
            # Still return 200 so Plaid doesn't hammer retries indefinitely.
            # (You may choose 500 to force retries.)
            return Response({"ok": True, "id": evt.id, "note": "recorded with error"}, status=200)

        # Respond quickly; Plaid expects a 2xx
        return Response({"ok": True, "id": evt.id}, status=200)
