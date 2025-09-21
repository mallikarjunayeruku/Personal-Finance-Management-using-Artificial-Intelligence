from django.db import migrations
from django.utils.text import slugify

SEED_CATEGORIES = [
    "Housing - Mortgage or rent",
    "Housing - Property taxes",
    "Housing - Household repairs",
    "Housing - HOA fees",
    "Transportation - Car payment",
    "Transportation - Car warranty",
    "Transportation - Gas",
    "Transportation - Tires",
    "Transportation - Maintenance and oil changes",
    "Transportation - Parking fees",
    "Transportation - Repairs",
    "Transportation - Registration and DMV Fees",
    "Food - Groceries",
    "Food - Restaurants",
    "Food - Pet food",
    "Utilities - Electricity",
    "Utilities - Water",
    "Utilities - Garbage",
    "Utilities - Phones",
    "Utilities - Cable",
    "Utilities - Internet",
    "Clothing - Adults’ clothing",
    "Clothing - Adults’ shoes",
    "Clothing - Children’s clothing",
    "Clothing - Children’s shoes",
    "Medical/Healthcare - Primary care",
    "Medical/Healthcare - Dental care",
    "Medical/Healthcare - Specialty care (dermatologists, orthodontics, optometrists, etc.)",
    "Medical/Healthcare - Urgent care",
    "Medical/Healthcare - Medications",
    "Medical/Healthcare - Medical devices",
    "Insurance - Health insurance",
    "Insurance - Homeowner’s or renter’s insurance",
    "Insurance - Home warranty or protection plan",
    "Insurance - Auto insurance",
    "Insurance - Life insurance",
    "Insurance - Disability insurance",
    "Household Items/Supplies - Toiletries",
    "Household Items/Supplies - Laundry detergent",
    "Household Items/Supplies - Dishwasher detergent",
    "Household Items/Supplies - Cleaning supplies",
    "Household Items/Supplies - Tools",
    "Personal - Gym memberships",
    "Personal - Haircuts",
    "Personal - Salon services",
    "Personal - Cosmetics (like makeup or services like laser hair removal)",
    "Personal - Babysitter",
    "Personal - Subscriptions",
    "Debt - Personal loans",
    "Debt - Student loans",
    "Debt - Credit cards",
    "Retirement - Financial planning",
    "Retirement - Investing",
    "Education - Children’s college",
    "Education - Your college",
    "Education - School supplies",
    "Education - Books",
    "Savings - Emergency fund",
    "Savings - Big purchases like a new mattress or laptop",
    "Savings - Other savings",
    "Gifts/Donations - Birthday",
    "Gifts/Donations - Anniversary",
    "Gifts/Donations - Wedding",
    "Gifts/Donations - Christmas",
    "Gifts/Donations - Special occasion",
    "Gifts/Donations - Charities",
    "Entertainment - Alcohol and/or bars",
    "Entertainment - Games",
    "Entertainment - Movies",
    "Entertainment - Concerts",
    "Entertainment - Vacations",
    "Entertainment - Subscriptions (Netflix, Amazon, Hulu, etc.)",
    "Others",
    "Unknown"
]

def unique_slug(existing_slugs: set[str], base_name: str, max_len: int = 100) -> str:
    base = slugify(base_name or "") or "category"
    base = base[:max_len]
    cand = base
    i = 2
    while cand in existing_slugs:
        suffix = f"-{i}"
        cand = (base[: max_len - len(suffix)]) + suffix
        i += 1
    existing_slugs.add(cand)
    return cand

def unique_name(existing_names: set[str], name: str, max_len: int = 80) -> str:
    """Ensure name fits in max_len and is unique among existing_names."""
    raw = (name or "").strip()
    if len(raw) <= max_len and raw not in existing_names:
        existing_names.add(raw)
        return raw

    base = raw[:max_len]
    cand = base
    i = 2
    while cand in existing_names or len(cand) > max_len:
        suffix = f" {i}"  # or "-{i}"
        cand = (base[: max_len - len(suffix)]) + suffix
        i += 1
    existing_names.add(cand)
    return cand

def seed_categories(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    existing_names = set(Category.objects.values_list("name", flat=True))
    existing_slugs = set(Category.objects.values_list("slug", flat=True))

    for name in SEED_CATEGORIES:
        norm_name = unique_name(existing_names, name, max_len=80)
        # ensure slug too
        slug = unique_slug(existing_slugs, norm_name, max_len=100)
        obj = Category.objects.filter(name=norm_name).first()
        if obj:
            if not obj.slug:
                obj.slug = slug
                obj.save(update_fields=["slug"])
            continue
        Category.objects.create(name=norm_name, slug=slug)

def backfill_category_fk(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    Transactions = apps.get_model("finance", "Transactions")
    existing_names = set(Category.objects.values_list("name", flat=True))
    existing_slugs = set(Category.objects.values_list("slug", flat=True))

    # Map normalized name -> id
    lut = {c.name.strip().lower(): c.id for c in Category.objects.all()}

    for tx in Transactions.objects.all().only("id", "category_fk"):
        raw = tx.__dict__.get("category")  # legacy text field value pre-drop
        if not raw or tx.category_fk_id:
            continue
        key = str(raw).strip().lower()

        cat_id = lut.get(key)
        if not cat_id:
            norm_name = unique_name(existing_names, str(raw).strip(), max_len=80)
            slug = unique_slug(existing_slugs, norm_name, max_len=100)
            obj = Category.objects.create(name=norm_name, slug=slug)
            cat_id = obj.id
            lut[norm_name.strip().lower()] = cat_id

        Transactions.objects.filter(pk=tx.pk).update(category_fk_id=cat_id)

def forwards(apps, schema_editor):
    seed_categories(apps, schema_editor)
    backfill_category_fk(apps, schema_editor)

class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0002_category_schema"),
    ]
    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
