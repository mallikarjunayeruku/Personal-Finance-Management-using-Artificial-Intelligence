import json
from pathlib import Path
from warnings import catch_warnings

from django.core.management.base import BaseCommand
from finance.models import Category

class Command(BaseCommand):
    help = "Import Plaid category JSON into Category table"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to Plaid categories JSON file")

    def handle(self, *args, **options):
        path = Path(options["json_path"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return

        data = json.loads(path.read_text())
        count_created, count_skipped = 0, 0

        for entry in data:
            pfcs = entry.get("possible_pfcs") or []
            for p in pfcs:
                primary = (p.get("primary") or "").strip()
                desc = (p.get("detailed") or "").strip()
                if not primary:
                    continue

                obj, created = Category.objects.get_or_create(name=primary, description=desc)
                if created:
                    count_created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created: {primary}"))
                else:
                    count_skipped += 1


        self.stdout.write(
            self.style.SUCCESS(f"Done. Created {count_created}, skipped {count_skipped} (already existed).")
        )
