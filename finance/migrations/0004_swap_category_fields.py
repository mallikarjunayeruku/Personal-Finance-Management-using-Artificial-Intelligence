# finance/migrations/0004_swap_category_fields.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0003_seed_categories_and_backfill"),
    ]

    operations = [
        # Drop the legacy text column. If your legacy field name differs, change this.
        migrations.RemoveField(
            model_name="transactions",
            name="category",
        ),
        # Rename category_fk -> category (final FK name)
        migrations.RenameField(
            model_name="transactions",
            old_name="category_fk",
            new_name="category",
        ),
    ]
