import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from audit.models import AuditLog
from audit.services import log_event
from imaging.file_utils import delete_file_if_exists
from imaging.models import Dataset, DatasetImage
from imaging.validators import validate_image_file


# Bulk-imports a Food-101 style folder (one sub-folder per class, images inside) into imaging.Dataset / imaging.DatasetImage.
#
#   python manage.py import_food101 /path/to/food-101/images --owner-email you@example.com --dataset-name "food-101" --limit-per-class 100
#
# Images are COPIED into MEDIA_ROOT/datasets/<dataset_id>/<class_label>/<uuid>.<ext> through the model's own upload_to,
# so the training pipeline (which reads DatasetImage.image.path) works exactly as it does for images uploaded through the UI/API.
# Re-running is safe: classes that already hold `--limit-per-class` images are skipped, partially filled classes are topped up.
class Command(BaseCommand):
    help = "Import a Food-101 style directory (class-per-folder) into a Dataset."

    def add_arguments(self, parser):
        parser.add_argument('dataset_path', help="Folder that contains one sub-folder per class, e.g. .../food-101/images")
        parser.add_argument('--owner-email', required=True, help="Email of an existing user; recorded as Dataset.created_by / DatasetImage.uploaded_by.")
        parser.add_argument('--dataset-name', default='food-101', help="Dataset name (created if missing, reused if it exists). Default: food-101")
        parser.add_argument('--description', default='Imported from Food-101.', help="Description used only when the dataset is created.")
        parser.add_argument('--limit-per-class', type=int, default=0, help="Max images per class in the dataset. 0 = import everything (default).")
        parser.add_argument('--batch-size', type=int, default=500, help="Rows inserted per DB batch. Default: 500")
        parser.add_argument('--no-validate', action='store_true', help="Skip the Pillow integrity check on each file (faster, less safe).")
        parser.add_argument('--dry-run', action='store_true', help="Scan and report what would be imported; write nothing.")

    def handle(self, *args, **options):
        root = Path(options['dataset_path']).expanduser().resolve()
        # Tolerate being pointed at the food-101 root instead of food-101/images.
        if not root.is_dir():
            raise CommandError(f"Not a directory: {root}")
        if (root / 'images').is_dir():
            root = root / 'images'

        limit = options['limit_per_class']
        batch_size = max(1, options['batch_size'])
        dry_run = options['dry_run']
        validate = not options['no_validate']
        allowed_ext = {e.lower() for e in getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp'])}

        class_dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith('.'))
        if not class_dirs:
            raise CommandError(f"No class sub-folders found in {root}. Point at the folder that contains apple_pie/, baby_back_ribs/, ...")

        User = get_user_model()
        try:
            owner = User.objects.get(email__iexact=options['owner_email'])
        except User.DoesNotExist:
            raise CommandError(
                f"No user with email '{options['owner_email']}'. Create one first with `python manage.py createsuperuser` "
                f"(this project's User also needs a phone number).")

        self.stdout.write(f"Source     : {root}")
        self.stdout.write(f"Classes    : {len(class_dirs)}")
        self.stdout.write(f"Per class  : {limit if limit else 'all'}")
        self.stdout.write(f"Owner      : {owner.email}")
        self.stdout.write(f"MEDIA_ROOT : {settings.MEDIA_ROOT}")

        if dry_run:
            dataset = Dataset.objects.filter(name=options['dataset_name']).first()
        else:
            dataset, created = Dataset.objects.get_or_create(
                name=options['dataset_name'],
                defaults={
                    'description': options['description'],
                    'created_by': owner
                })
            self.stdout.write(f"Dataset    : '{dataset.name}' (id={dataset.id}, {'created' if created else 'existing'})")

        totals = {'imported': 0, 'skipped_existing': 0, 'invalid': 0}
        batch = []

        for class_dir in class_dirs:
            label = class_dir.name
            files = sorted(
                f for f in class_dir.iterdir()
                if f.is_file() and not f.name.startswith('.') and f.suffix.lower() in allowed_ext)

            existing = DatasetImage.objects.filter(dataset=dataset, class_label=label).count() if dataset else 0
            wanted = files[:limit] if limit else files
            todo = wanted[existing:]
            totals['skipped_existing'] += min(existing, len(wanted))

            class_imported = 0
            for path in todo:
                if dry_run:
                    class_imported += 1
                    continue

                instance = DatasetImage(dataset=dataset, class_label=label, uploaded_by=owner)
                try:
                    with open(path, 'rb') as fh:
                        django_file = File(fh, name=path.name)
                        if validate:
                            validate_image_file(django_file)
                        instance.image.save(path.name, django_file, save=False)
                except ValidationError as exc:
                    totals['invalid'] += 1
                    self.stderr.write(f"  skipped {label}/{path.name}: {'; '.join(exc.messages)}")
                    continue
                except OSError as exc:
                    totals['invalid'] += 1
                    self.stderr.write(f"  skipped {label}/{path.name}: {exc}")
                    continue

                batch.append(instance)
                class_imported += 1
                if len(batch) >= batch_size:
                    self._flush(batch)
                    batch = []

            totals['imported'] += class_imported
            self.stdout.write(f"  {label:<28} +{class_imported:<5} (already had {existing}, found {len(files)} files)")

        if batch:
            self._flush(batch)

        verb = 'Would import' if dry_run else 'Imported'
        self.stdout.write(self.style.SUCCESS(
            f"\n{verb} {totals['imported']} images "
            f"({totals['skipped_existing']} already present, {totals['invalid']} skipped as invalid)."))

        if not dry_run and totals['imported']:
            log_event(
                AuditLog.EventType.IMAGE_UPLOADED,
                user=owner,
                description=f"Bulk-imported {totals['imported']} images into dataset '{dataset.name}' via import_food101.",
                metadata={'source': str(root), 'limit_per_class': limit, **totals},
                reference_model='Dataset',
                reference_id=dataset.id)
            self.stdout.write(f"Dataset '{dataset.name}' now has {dataset.get_num_images()} images in {dataset.get_num_classes()} classes.")

    # Inserts one batch of already-stored files as DB rows. If the insert fails, the files just written to MEDIA_ROOT are removed so no orphans are left behind.
    def _flush(self, batch):
        try:
            with transaction.atomic():
                DatasetImage.objects.bulk_create(batch)
        except Exception:
            for instance in batch:
                delete_file_if_exists(instance.image)
            raise
