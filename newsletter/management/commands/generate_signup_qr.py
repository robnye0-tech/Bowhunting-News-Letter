from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    help = (
        "Generate a QR code PNG that links straight to the signup page (email + "
        "up to 3 states). Encodes SITE_BASE_URL from .env by default, so set that "
        "to your real public domain before generating one to print or share."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default=None,
            help="Override the URL to encode instead of using SITE_BASE_URL + the signup page.",
        )
        parser.add_argument(
            "--out",
            default="qr_codes/signup_qr.png",
            help="Output path for the PNG, relative to the project root by default.",
        )

    def handle(self, *args, **options):
        import qrcode

        target_url = options["url"] or f"{settings.SITE_BASE_URL}{reverse('newsletter:home')}"

        out_path = Path(options["out"])
        if not out_path.is_absolute():
            out_path = Path(settings.BASE_DIR) / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)

        img = qrcode.make(target_url)
        img.save(out_path)

        self.stdout.write(self.style.SUCCESS(f"QR code encoding: {target_url}"))
        self.stdout.write(self.style.SUCCESS(f"Saved to: {out_path}"))

        if "127.0.0.1" in target_url or "localhost" in target_url:
            self.stdout.write(
                self.style.WARNING(
                    "This points at a local address — it will only work on devices on "
                    "your own machine. Set SITE_BASE_URL in .env to your real public "
                    "domain before printing or sharing this QR code."
                )
            )
        self.stdout.write("Test-scan it with your phone before printing or distributing it.")
