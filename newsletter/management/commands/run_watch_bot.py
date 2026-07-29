import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from newsletter.aggregation import process_page_source, process_rss_source
from newsletter.models import ContentSource, current_week_of

DEFAULT_OUTPUT_DIR = "scraped_updates"


class Command(BaseCommand):
    help = (
        "The 'bot' you turn on and off: continuously watches every active content "
        "source (RSS feeds and plain pages) for new or changed content. RSS finds "
        "become draft ContentItems in the admin, same as aggregate_content. Plain "
        "pages are checked for changed text; when one changes, a snapshot file is "
        "written to a folder for you to read AND a draft ContentItem is created. "
        "Start it and leave it running; stop it with Ctrl+C or by closing the "
        "window. Use --once for a single pass instead (e.g. from Task Scheduler)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Run a single pass and exit, instead of looping."
        )
        parser.add_argument(
            "--interval", type=int, default=6, help="Hours between passes when looping (default: 6)."
        )
        parser.add_argument(
            "--out", default=DEFAULT_OUTPUT_DIR, help="Folder to write changed-page snapshots into."
        )

    def handle(self, *args, **options):
        output_root = settings.BASE_DIR / options["out"]
        once = options["once"]
        interval_hours = options["interval"]

        self.stdout.write(self.style.SUCCESS(f"Watch bot starting. Findings will be written to: {output_root}"))
        if not once:
            self.stdout.write(
                f"Checking every {interval_hours} hour(s). Press Ctrl+C or close this window to stop."
            )

        try:
            while True:
                self._run_pass(output_root)
                if once:
                    break
                self.stdout.write(f"Sleeping {interval_hours}h until the next check...")
                time.sleep(interval_hours * 3600)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nStopped."))

    def _run_pass(self, output_root):
        week_of = current_week_of()
        sources = list(ContentSource.objects.filter(active=True).select_related("state"))

        rss_new = 0
        pages_changed = 0
        errors = []

        for source in sources:
            if source.source_type == ContentSource.SourceType.RSS:
                created, error = process_rss_source(source, week_of)
                rss_new += created
            else:
                changed, error = process_page_source(source, week_of, output_root)
                pages_changed += int(changed)

            if error:
                errors.append(f"{source}: {error}")

        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        self.stdout.write(
            f"[{timestamp}] checked {len(sources)} source(s) — "
            f"{rss_new} new RSS item(s), {pages_changed} page(s) changed."
        )
        for err in errors:
            self.stderr.write(self.style.WARNING(err))
