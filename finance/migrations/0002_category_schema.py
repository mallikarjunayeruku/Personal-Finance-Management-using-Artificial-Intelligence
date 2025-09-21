# finance/migrations/0002_category_schema.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),  # <-- adjust if your first migration has a different name
    ]

    operations = [
        # 1) Create Category table
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=100, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),

        # 2) Add a temporary FK field to Transactions (nullable)
        #    We keep the existing text category column as-is for now.
        migrations.AddField(
            model_name="transactions",
            name="category_fk",
            field=models.ForeignKey(
                to="finance.category",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                null=True,
                blank=True,
            ),
        ),
    ]
