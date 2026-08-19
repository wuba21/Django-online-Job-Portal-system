import os
import shutil
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from resume_cv.models import ResumeCvCategory, ResumeCvTemplate

class Command(BaseCommand):
    help = "Seeds resume categories, templates, and thumbnail images"

    def handle(self, *args, **options):
        self.stdout.write("Seeding resume templates...")

        # 1. Ensure media directories exist
        media_target = os.path.join(settings.MEDIA_ROOT, "resumes", "2022", "03", "28")
        os.makedirs(media_target, exist_ok=True)

        # 2. Copy static thumbnails to media folder
        static_source = os.path.join(settings.BASE_DIR, "static", "img", "resume-thumbnails")
        if os.path.exists(static_source):
            for filename in os.listdir(static_source):
                src_file = os.path.join(static_source, filename)
                dst_file = os.path.join(media_target, filename)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
            self.stdout.write(self.style.SUCCESS(f"Copied thumbnails to {media_target}"))
        else:
            self.stdout.write(self.style.WARNING(f"Static source {static_source} not found"))

        # 3. Load fixture data from JSON file
        fixture_path = os.path.join(settings.BASE_DIR, "resume_cv", "fixtures", "resume_templates.json")
        if os.path.exists(fixture_path):
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            categories_count = 0
            templates_count = 0

            for item in data:
                model_name = item.get("model")
                pk = item.get("pk")
                fields = item.get("fields")

                if model_name == "resume_cv.resumecvcategory":
                    cat, created = ResumeCvCategory.objects.update_or_create(
                        pk=pk,
                        defaults={
                            "name": fields.get("name"),
                            "color": fields.get("color", "Black"),
                        }
                    )
                    categories_count += 1
                elif model_name == "resume_cv.resumecvtemplate":
                    cat_id = fields.get("category")
                    template, created = ResumeCvTemplate.objects.update_or_create(
                        pk=pk,
                        defaults={
                            "category_id": cat_id,
                            "name": fields.get("name"),
                            "thumbnail": fields.get("thumbnail"),
                            "content": fields.get("content", ""),
                            "style": fields.get("style", ""),
                            "active": fields.get("active", True),
                            "is_premium": fields.get("is_premium", False),
                        }
                    )
                    templates_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Successfully seeded {categories_count} categories and {templates_count} templates!"
            ))
        else:
            self.stdout.write(self.style.ERROR(f"Fixture file not found at {fixture_path}"))
