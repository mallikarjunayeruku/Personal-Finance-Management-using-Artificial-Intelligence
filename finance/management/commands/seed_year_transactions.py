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
    """Round to 2 decimals (banker's rounding not needed here)."""
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
    help = (
        "Seed up to one year of transactions for a user and update account balances.\n"
        "Includes Salary (7500) + common expenses, random unknowns.\n\n"
        "Examples:\n"
        "  python manage.py seed_year_transactions --username alice --months 12\n"
        "  python manage.py seed_year_transactions --user-id 5 --months 6 --start-year 2024 --start-month 4\n"
        "  python manage.py seed_year_transactions --username alice --checking-id 3 --credit-id 7 --bill-id 3\n"
        "  python manage.py seed_year_transactions --username alice --months 12 --dry-run --monthly-cap 2000 --rng-seed 42\n"
    )

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group(required=True)
        g.add_argument("--username", type=str, help="Username of the owner")
        g.add_argument("--user-id", type=int, help="User ID of the owner")

        parser.add_argument("--months", type=int, default=12, help="How many months to generate (max 12)")
        parser.add_argument("--start-year", type=int, default=timezone.now().year, help="Start year (default: current)")
        parser.add_argument("--start-month", type=int, default=timezone.now().month, help="Start month as 1-12 (default: current month)")
        parser.add_argument("--checking-id", type=int, help="Account ID to use as primary checking/current (expenses & salary)")
        parser.add_argument("--credit-id", type=int, help="Account ID to use as credit card (shopping/gas/movies etc.)")
        parser.add_argument("--bill-id", type=int, help="Account ID to use to pay bills (mobile/wifi/electricity/maintenance)")
        parser.add_argument("--random-unknown", type=int, default=3, help="Random unknown/other/empty transactions per month")

        # New flags
        parser.add_argument("--dry-run", action="store_true", help="Simulate only: no DB writes, show summary")
        parser.add_argument("--monthly-cap", type=float, default=None,
                            help="Cap monthly EXPENSES (USD). Salary still posts in full.")
        parser.add_argument("--rng-seed", type=int, default=None, help="Seed the RNG for reproducible data")

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

        months = max(1, min(12, int(opts["months"])))
        start_year = int(opts["start_year"])
        start_month = int(opts["start_month"])
        if not (1 <= start_month <= 12):
            raise CommandError("--start-month must be 1..12")

        monthly_cap = None if opts["monthly_cap"] is None else Decimal(str(opts["monthly_cap"])).quantize(Decimal("0.01"))
        dry_run = bool(opts["dry_run"])

        accounts = list(Account.objects.filter(user=user).order_by("id"))
        if not accounts:
            raise CommandError(f"No accounts found for user {user}")

        # Choose accounts
        acc_checking = Account.objects.filter(user=user, id=opts.get("checking_id")).first() if opts.get("checking_id") else None
        acc_credit   = Account.objects.filter(user=user, id=opts.get("credit_id")).first() if opts.get("credit_id") else None
        acc_bills    = Account.objects.filter(user=user, id=opts.get("bill_id")).first() if opts.get("bill_id") else None

        if not acc_checking:
            acc_checking = pick_account_by_type(accounts, ("checking", "current", "savings"))
        if not acc_credit:
            acc_credit = pick_account_by_type(accounts, ("credit",))
        if not acc_bills:
            acc_bills = acc_checking

        # Merchant pools
        groceries_merchants = ["Ralphs", "Vons", "Trader Joe's", "Whole Foods", "Safeway"]
        food_merchants = ["Starbucks", "Chick-fil-A", "McDonalds", "Panera Bread", "Dunkin Donuts"]
        shopping_merchants = ["Target", "Best Buy", "Amazon", "Costco", "Walmart"]
        movies_merchants = ["AMC", "Cinemark", "Regal", "Netflix", "Hulu"]
        gas_merchants = ["Shell", "Chevron", "Mobil", "76", "Arco"]
        zelle_merchants = ["Zelle Transfer", "Zelle Payment", "Zelle Incoming"]

        # Categories (ensure exist)
        cat_salary        = upsert_category(88)
        cat_groceries     = upsert_category(52)
        cat_food          = upsert_category(23)
        cat_shopping      = upsert_category(74)
        cat_movies        = upsert_category(36)
        cat_gas           = upsert_category(57)
        cat_zelle         = upsert_category(51)
        cat_mobile        = upsert_category(64)
        cat_wifi          = upsert_category(43)
        cat_electricity   = upsert_category(67)
        cat_maintenance   = upsert_category(53)
        cat_unknown       = upsert_category(99)
        cat_other         = upsert_category(98)

        def month_plan(year, month):
            dt = rand_dt_in_month(year, month)
            plan = []

            # Salary (income)
            plan.append({
                "name": "Monthly Salary",
                "merchant": "Employer Inc",
                "category": cat_salary,
                "amount": Decimal("7500.00"),
                "is_income": True,
                "account": acc_checking,
                "date": dt.replace(day=random.randint(1, 5)),
            })

            # Bills
            plan += [
                {"name": "T-Mobile", "merchant": "T-Mobile", "category": cat_mobile, "amount": Decimal("54.00"), "is_income": False, "account": acc_bills, "date": dt.replace(day=8)},
                {"name": "WiFi Bill", "merchant": "Comcast", "category": cat_wifi, "amount": Decimal(random.choice([55, 60, 65])), "is_income": False, "account": acc_bills, "date": dt.replace(day=10)},
                {"name": "Electricity Bill", "merchant": "PG&E", "category": cat_electricity, "amount": Decimal(random.choice([80, 95, 110, 130])), "is_income": False, "account": acc_bills, "date": dt.replace(day=12)},
                {"name": "House Maintenance", "merchant": "Local Services", "category": cat_maintenance, "amount": Decimal(random.choice([40, 60, 75, 90])), "is_income": False, "account": acc_bills, "date": dt.replace(day=18)},
            ]

            # Groceries (2–4)
            for _ in range(random.randint(2, 4)):
                plan.append({
                    "name": "Groceries",
                    "merchant": random.choice(groceries_merchants),
                    "category": cat_groceries,
                    "amount": Decimal(random.randrange(30, 140)),
                    "is_income": False,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Food (2–5)
            for _ in range(random.randint(2, 5)):
                plan.append({
                    "name": "Food",
                    "merchant": random.choice(food_merchants),
                    "category": cat_food,
                    "amount": Decimal(random.randrange(8, 28)),
                    "is_income": False,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Shopping (1–3) prefer credit
            for _ in range(random.randint(1, 3)):
                plan.append({
                    "name": "Shopping",
                    "merchant": random.choice(shopping_merchants),
                    "category": cat_shopping,
                    "amount": Decimal(random.randrange(25, 220)),
                    "is_income": False,
                    "account": acc_credit or acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Movies/leisure (0–2)
            for _ in range(random.randint(0, 2)):
                plan.append({
                    "name": "Movies & Leisure",
                    "merchant": random.choice(movies_merchants),
                    "category": cat_movies,
                    "amount": Decimal(random.randrange(10, 40)),
                    "is_income": False,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Gas (1–3)
            for _ in range(random.randint(1, 3)):
                plan.append({
                    "name": "Gas",
                    "merchant": random.choice(gas_merchants),
                    "category": cat_gas,
                    "amount": Decimal(random.randrange(35, 85)),
                    "is_income": False,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Zelle (0–2 in/out)
            for _ in range(random.randint(0, 2)):
                is_in = bool(random.getrandbits(1))
                plan.append({
                    "name": "Zelle Transfer In" if is_in else "Zelle Transfer Out",
                    "merchant": random.choice(zelle_merchants),
                    "category": cat_zelle,
                    "amount": Decimal(random.randrange(20, 300)),
                    "is_income": is_in,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            # Unknown/Other/Empty
            for _ in range(int(opts["random_unknown"])):
                chosen = random.choice([
                    {"cat": cat_unknown, "name": ""},
                    {"cat": cat_other, "name": "Misc"},
                    {"cat": None, "name": ""},  # empty category
                ])
                plan.append({
                    "name": chosen["name"] or "Misc",
                    "merchant": "N/A",
                    "category": chosen["cat"],
                    "amount": Decimal(random.randrange(5, 60)),
                    "is_income": False,
                    "account": acc_checking,
                    "date": rand_dt_in_month(year, month),
                })

            return plan

        # apply cap to expense items (salary not capped)
        def apply_monthly_cap(items, cap: Decimal):
            if cap is None:
                return items
            # Split income/expense
            incomes = [it for it in items if it["is_income"]]
            expenses = [it for it in items if not it["is_income"]]

            total_expense = sum((it["amount"] for it in expenses), Decimal("0"))
            total_expense = money(total_expense)

            if total_expense <= cap:
                return incomes + expenses  # nothing to change

            # Strategy:
            # 1) Sort expenses descending (reduce large first), scale them down proportionally,
            #    but keep small transactions at least $1 to look realistic.
            # 2) If still over cap due to minimums, drop the smallest ones until under cap.
            scale = (cap / total_expense) if total_expense > 0 else Decimal("1")
            scaled = []
            for it in sorted(expenses, key=lambda x: x["amount"], reverse=True):
                new_amt = money(it["amount"] * scale)
                if new_amt < Decimal("1.00"):
                    new_amt = Decimal("1.00")
                it2 = it.copy()
                it2["amount"] = new_amt
                scaled.append(it2)

            # Re-check and trim if slight overflow due to floors
            cur = sum((it["amount"] for it in scaled), Decimal("0"))
            cur = money(cur)
            if cur > cap:
                # drop small ones until <= cap
                scaled.sort(key=lambda x: x["amount"])  # smallest first
                i = 0
                while i < len(scaled) and cur > cap:
                    cur = money(cur - scaled[i]["amount"])
                    i += 1
                scaled = scaled[i:]

            return incomes + scaled

        # ---------- execution ----------
        created = 0
        months_done = 0
        y, m = start_year, start_month

        # Track dry-run balance impacts (account_id -> Decimal delta)
        balance_deltas = {}

        ctx_mgr = transaction.atomic if not dry_run else _nullcontext  # type: ignore
        with ctx_mgr():
            for _ in range(months):
                items = month_plan(y, m)
                if monthly_cap is not None:
                    items = apply_monthly_cap(items, monthly_cap)

                # sort by date for realism
                items.sort(key=lambda x: x["date"])

                # monthly totals for logging
                month_income = Decimal("0")
                month_expense = Decimal("0")

                for it in items:
                    acc = it["account"]
                    if not acc:
                        continue

                    is_income = bool(it["is_income"])
                    amt = money(it["amount"])
                    delta = amt if is_income else (amt * Decimal("-1"))

                    if dry_run:
                        # track net effect
                        balance_deltas[acc.id] = balance_deltas.get(acc.id, Decimal("0")) + delta
                        if is_income:
                            month_income += amt
                        else:
                            month_expense += amt
                        continue

                    tx = Transactions.objects.create(
                        user=user,
                        ownerId=str(user.id) if hasattr(Transactions, "ownerId") else None,
                        amount=float(amt),
                        category=it["category"],
                        name=it["name"] or "Misc",
                        merchantName=it["merchant"],
                        currencyCode="USD",
                        note=f"seeded{' (cap)' if monthly_cap is not None else ''}",
                        createdDate=it["date"],
                        transactionDate=it["date"],
                        location=None,
                        latitude=None,
                        longitude=None,
                        path=None,
                        isIncome=is_income,
                        repeat=None,
                        account=acc,
                        isCashAccount=False,
                        canDelete=True,
                    )
                    bump_balance(acc.id, delta)
                    created += 1
                    if is_income:
                        month_income += amt
                    else:
                        month_expense += amt

                months_done += 1
                self.stdout.write(self.style.NOTICE(
                    f"[{y:04d}-{m:02d}] income={month_income}  expenses={month_expense}  "
                    f"net={(month_income - month_expense).quantize(Decimal('0.01'))}"
                ))

                if m == 12:
                    y += 1
                    m = 1
                else:
                    m += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN — no DB writes performed."))
            if balance_deltas:
                self.stdout.write("Account balance impacts (simulated):")
                for acc_id, d in sorted(balance_deltas.items()):
                    self.stdout.write(f"  - Account {acc_id}: {money(d)}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nInserted {created} transactions across {months_done} month(s) for user '{user}'."
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Accounts used: checking={getattr(acc_checking, 'id', None)} "
            f"credit={getattr(acc_credit, 'id', None)} bills={getattr(acc_bills, 'id', None)}"
        ))

# --- small compat helper for dry-run ---
class _nullcontext:
    def __enter__(self): return None
    def __exit__(self, *exc): return False
