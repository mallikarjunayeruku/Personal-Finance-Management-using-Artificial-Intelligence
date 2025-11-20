# finance/management/commands/seed_year_transactions.py
import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from finance.models import Account, Transactions, Category

User = get_user_model()

# ---------- helpers ----------

def to_dec(n) -> Decimal:
    try:
        return Decimal(str(n))
    except Exception:
        return Decimal("0")


def money(n: Decimal) -> Decimal:
    """Round to 2 decimals"""
    return to_dec(n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def first_day(year: int, month: int) -> datetime:
    return datetime(year, month, 1, 10, 0, 0, tzinfo=timezone.get_current_timezone())


def rand_dt_in_month(year: int, month: int) -> datetime:
    start = first_day(year, month)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=start.tzinfo)
    else:
        end = datetime(year, month + 1, 1, tzinfo=start.tzinfo)
    delta_days = (end - start).days
    d = start + timedelta(days=random.randrange(delta_days), hours=random.randrange(8, 20))
    return d


def upsert_category(id: int) -> Category:
    cat, _ = Category.objects.get_or_create(id=id)
    return cat


def bump_balance(account_id, delta: Decimal):
    Account.objects.filter(id=account_id).update(
        currentBalance=Coalesce(F("currentBalance"), Value(0)) + delta
    )


def pick_account_by_type(accounts, type_keywords: tuple[str, ...]):
    for acc in accounts:
        t = (acc.accountType or "").lower()
        if any(k in t for k in type_keywords):
            return acc
    return accounts[0] if accounts else None


# ---------- command ----------

class Command(BaseCommand):
    help = "Seed up to one year of realistic transactions for a user."

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group(required=True)
        g.add_argument("--username", type=str, help="Username of the owner")
        g.add_argument("--user-id", type=int, help="User ID of the owner")

        parser.add_argument("--months", type=int, default=12)
        parser.add_argument("--start-year", type=int, default=timezone.now().year)
        parser.add_argument("--start-month", type=int, default=timezone.now().month)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--monthly-cap", type=float, default=None)
        parser.add_argument("--rng-seed", type=int, default=None)
        # in add_arguments(self, parser)
        parser.add_argument("--backfill-years", type=int, default=None,
                            help="If set, ignore start-year/month and generate from (now - N years) up to current month.")
        parser.add_argument("--backfill-months", type=int, default=None,
                            help="If set, ignore start-year/month and generate from (now - N months + 1) up to current month.")

    def handle(self, *args, **opts):
        if opts.get("rng_seed") is not None:
            random.seed(int(opts["rng_seed"]))

        # Resolve user
        if opts.get("username"):
            try:
                user = User.objects.get(username=opts["username"])
            except User.DoesNotExist:
                raise CommandError(f"User '{opts['username']}' not found")
        else:
            try:
                user = User.objects.get(pk=opts["user_id"])
            except User.DoesNotExist:
                raise CommandError(f"User id={opts['user_id']} not found")

        # existing:
        # months = max(1, min(12, int(opts["months"])))
        # start_year = int(opts["start_year"])
        # start_month = int(opts["start_month"])

        # NEW: helper to move by months
        def _shift_year_month(y: int, m: int, delta_months: int) -> tuple[int, int]:
            # delta_months can be negative
            total = (y * 12 + (m - 1)) + delta_months
            new_y, new_m_index = divmod(total, 12)
            return new_y, new_m_index + 1  # month back to 1..12

        today = timezone.localdate()
        cur_y, cur_m = today.year, today.month

        backfill_months = None
        if opts.get("backfill_years") is not None:
            backfill_months = int(opts["backfill_years"]) * 12
        elif opts.get("backfill_months") is not None:
            backfill_months = int(opts["backfill_months"])

        if backfill_months and backfill_months > 0:
            # include current month, go back (backfill_months - 1) months
            months = backfill_months
            start_year, start_month = _shift_year_month(cur_y, cur_m, -(months - 1))
        else:
            # fall back to explicit args (as before)
            months = max(1, min(120, int(opts["months"])))  # allow >12 if you like
            start_year = int(opts["start_year"])
            start_month = int(opts["start_month"])

        monthly_cap = (
            None
            if opts["monthly_cap"] is None
            else Decimal(str(opts["monthly_cap"])).quantize(Decimal("0.01"))
        )
        dry_run = bool(opts["dry_run"])

        accounts = list(Account.objects.filter(user=user).order_by("id"))
        if not accounts:
            raise CommandError(f"No accounts found for user {user}")

        acc_checking = pick_account_by_type(accounts, ("checking", "current", "savings"))
        acc_credit = pick_account_by_type(accounts, ("credit",))
        acc_bills = acc_checking

        # ---- categories ----
        cats = {
            "salary": upsert_category(88),
            "vehicle_ins": upsert_category(55),
            "health_ins": upsert_category(55),
            "mobile": upsert_category(64),
            "wifi": upsert_category(43),
            "rent": upsert_category(34),
            "netflix": upsert_category(36),
            "hulu": upsert_category(36),
            "prime": upsert_category(36),
            "transfer_in": upsert_category(51),
            "transfer_out": upsert_category(31),
            "food": upsert_category(22),
            "restaurant": upsert_category(20),
            "bar": upsert_category(21),
            "groceries": upsert_category(52),
            "shopping": upsert_category(74),
            "gas": upsert_category(57),
            "coffee": upsert_category(24),
            "travel": upsert_category(65),
            "flight": upsert_category(56),
            "hotel": upsert_category(92),
            "vehicle_service": upsert_category(53),
            "furnishing": upsert_category(54),
            "clothing": upsert_category(74),
            "donation": upsert_category(16),
            "credit_payment": upsert_category(33),
        }

        # Merchant pools
        merchants = {
            "vehicle_ins": ["GEICO", "Progressive"],
            "health_ins": ["Anthem", "UnitedHealth"],
            "mobile": ["Verizon", "AT&T"],
            "wifi": ["Comcast", "Spectrum"],
            "rent": ["Apartment Rent", "Property Mgmt"],
            "netflix": ["Netflix"],
            "hulu": ["Hulu"],
            "prime": ["Amazon Prime"],
            "food": ["Chipotle", "Subway", "Panera", "Five Guys"],
            "restaurant": ["Olive Garden", "PF Chang’s", "Cheesecake Factory"],
            "bar": ["BJ’s", "Applebee’s", "Buffalo Wild Wings"],
            "groceries": ["Ralphs", "Trader Joe’s", "Safeway", "Vons"],
            "shopping": ["Target", "Best Buy", "Walmart"],
            "gas": ["Shell", "Chevron", "76", "Arco"],
            "coffee": ["Starbucks", "Dunkin Donuts"],
            "travel": ["Expedia", "TripAdvisor"],
            "flight": ["United Airlines", "Delta"],
            "hotel": ["Marriott", "Hilton", "Holiday Inn"],
            "vehicle_service": ["Jiffy Lube", "Midas", "Firestone"],
            "furnishing": ["IKEA", "Home Depot"],
            "clothing": ["H&M", "Macy’s"],
            "donation": ["Red Cross", "CSUDH Foundation"],
        }

        def month_plan(year, month):
            dt = rand_dt_in_month(year, month)
            plan = []

            # === INCOME ===
            salary_amt = Decimal(random.randrange(4400, 4700))
            plan.append({
                "name": "Monthly Salary",
                "merchant": "Employer Inc",
                "category": cats["salary"],
                "amount": salary_amt,
                "is_income": True,
                "account": acc_checking,
                "date": dt.replace(day=random.randint(1, 5)),
            })

            # === Monthly Fixed Expenses ===
            monthly_fixes = [
                ("Vehicle Insurance", "vehicle_ins", 190, 190),  # fixed 190
                ("Health Insurance", "health_ins", 120, 120),  # fixed 120
                ("Mobile Bill", "mobile", 50, 70),
                ("WiFi Bill", "wifi", 50, 70),
                ("House Rent & Utilities", "rent", 1500, 1500),  # fixed 1500
                ("Netflix", "netflix", 15.99, 15.99),
                ("Hulu", "hulu", 14.99, 14.99),
                ("Amazon Prime", "prime", 14.99, 14.99),
            ]
            for name, key, lo, hi in monthly_fixes:
                plan.append({
                    "name": name,
                    "merchant": random.choice(merchants[key]),
                    "category": cats[key],
                    "amount": Decimal(str(round(random.uniform(lo, hi), 2))),
                    "is_income": False,
                    "account": acc_bills,
                    "date": rand_dt_in_month(year, month),
                })

            # === Transfers ===
            plan += [
                {"name": "Zelle Transfer In", "merchant": "Zelle", "category": cats["transfer_in"],
                 "amount": Decimal(random.randrange(200, 500)), "is_income": True, "account": acc_checking,
                 "date": rand_dt_in_month(year, month)},
                {"name": "Zelle Transfer Out", "merchant": "Venmo", "category": cats["transfer_out"],
                 "amount": Decimal(random.randrange(50, 200)), "is_income": False, "account": acc_checking,
                 "date": rand_dt_in_month(year, month)},
            ]

            # === Weekly Recurring ===
            weekly_keys = ["food", "restaurant", "bar", "groceries", "shopping", "gas", "coffee"]
            for wk in range(4):
                for key in weekly_keys:
                    amt = {
                        "food": (8, 28),
                        "restaurant": (20, 50),
                        "bar": (15, 40),
                        "groceries": (40, 120),
                        "shopping": (25, 100),
                        "gas": (35, 80),
                        "coffee": (5, 10),
                    }[key]
                    plan.append({
                        "name": key.capitalize(),
                        "merchant": random.choice(merchants[key]),
                        "category": cats[key],
                        "amount": Decimal(random.randrange(*amt)),
                        "is_income": False,
                        "account": acc_checking,
                        "date": rand_dt_in_month(year, month) + timedelta(days=wk*7),
                    })

            # === Quarterly (every 3 months) ===
            if (month - start_month) % 3 == 0:
                q_items = [
                    ("Travel & Vacation", "travel", 300, 800),
                    ("Flight Tickets", "flight", 250, 600),
                    ("Hotels", "hotel", 200, 500),
                    ("Vehicle Maintenance", "vehicle_service", 80, 250),
                    ("Home & Furnishings", "furnishing", 150, 400),
                    ("Cloth Shopping", "clothing", 80, 200),
                ]
                for name, key, lo, hi in q_items:
                    plan.append({
                        "name": name,
                        "merchant": random.choice(merchants[key]),
                        "category": cats[key],
                        "amount": Decimal(random.randrange(lo, hi)),
                        "is_income": False,
                        "account": acc_checking,
                        "date": rand_dt_in_month(year, month),
                    })

            # === Semiannual (every 6 months) ===
            if (month - start_month) % 6 == 0:
                s_items = [
                    ("Donation (College)", "donation", 100, 300),
                    ("Donation (Non-Profit)", "donation", 50, 200),
                ]
                for name, key, lo, hi in s_items:
                    plan.append({
                        "name": name,
                        "merchant": random.choice(merchants[key]),
                        "category": cats[key],
                        "amount": Decimal(random.randrange(lo, hi)),
                        "is_income": False,
                        "account": acc_checking,
                        "date": rand_dt_in_month(year, month),
                    })

            # === Credit Card Usage ===
            credit_txns = []
            for _ in range(random.randint(3, 6)):
                amt = Decimal(random.randrange(10, 60))
                credit_txns.append({
                    "name": "Grocery (Credit Card)",
                    "merchant": random.choice(merchants["groceries"]),
                    "category": cats["groceries"],
                    "amount": amt,
                    "is_income": False,
                    "account": acc_credit or acc_checking,
                    "date": rand_dt_in_month(year, month),
                })
            plan.extend(credit_txns)

            # === Credit Card Repayment (next month) ===
            total_credit = sum((x["amount"] for x in credit_txns), Decimal("0"))
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            plan.append({
                "name": "Credit Card Payment",
                "merchant": "Credit Card AutoPay",
                "category": cats["credit_payment"],
                "amount": total_credit,
                "is_income": False,
                "account": acc_checking,
                "date": first_day(next_year, next_month),
            })

            return plan

        def apply_monthly_cap(items, cap: Decimal):
            if cap is None:
                return items
            incomes = [it for it in items if it["is_income"]]
            expenses = [it for it in items if not it["is_income"]]
            total_expense = sum((it["amount"] for it in expenses), Decimal("0"))
            if total_expense <= cap:
                return items

            scale = cap / total_expense
            scaled = []
            for it in expenses:
                new_amt = money(it["amount"] * scale)
                if new_amt < Decimal("1.00"):
                    new_amt = Decimal("1.00")
                it2 = it.copy()
                it2["amount"] = new_amt
                scaled.append(it2)
            return incomes + scaled

        # ---- execute ----
        created, months_done = 0, 0
        y, m = start_year, start_month
        balance_deltas = {}

        ctx_mgr = transaction.atomic if not dry_run else _nullcontext  # type: ignore
        with ctx_mgr():
            for _ in range(months):
                # monthly cap variation
                effective_cap = monthly_cap or Decimal(random.randrange(400, 4000))
                items = month_plan(y, m)
                items = apply_monthly_cap(items, effective_cap)

                items.sort(key=lambda x: x["date"])
                month_income = sum((it["amount"] for it in items if it["is_income"]), Decimal("0"))
                month_expense = sum((it["amount"] for it in items if not it["is_income"]), Decimal("0"))

                for it in items:
                    acc = it["account"]
                    if not acc:
                        continue
                    is_income = bool(it["is_income"])
                    amt = money(it["amount"])
                    delta = amt if is_income else -amt

                    if dry_run:
                        balance_deltas[acc.id] = balance_deltas.get(acc.id, Decimal("0")) + delta
                        continue

                    Transactions.objects.create(
                        user=user,
                        ownerId=str(user.id),
                        amount=float(amt),
                        category=it["category"],
                        name=it["name"],
                        merchantName=it["merchant"],
                        currencyCode="USD",
                        note=f"seeded realistic",
                        createdDate=it["date"],
                        transactionDate=it["date"],
                        isIncome=is_income,
                        account=acc,
                        isCashAccount=False,
                        canDelete=True,
                    )
                    bump_balance(acc.id, delta)
                    created += 1

                months_done += 1
                self.stdout.write(self.style.NOTICE(
                    f"[{y:04d}-{m:02d}] income={month_income}  expenses={month_expense}  net={(month_income - month_expense).quantize(Decimal('0.01'))}"
                ))

                if m == 12:
                    y += 1
                    m = 1
                else:
                    m += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN — no DB writes performed."))
            if balance_deltas:
                self.stdout.write("Simulated account balance impacts:")
                for acc_id, d in sorted(balance_deltas.items()):
                    self.stdout.write(f"  - Account {acc_id}: {money(d)}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nInserted {created} transactions across {months_done} month(s) for user '{user}'."
            ))


# --- context helper for dry-run ---
class _nullcontext:
    def __enter__(self): return None
    def __exit__(self, *exc): return False
