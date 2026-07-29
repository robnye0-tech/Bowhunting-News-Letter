from django.core.management.base import BaseCommand

from newsletter.aggregation import process_rss_source
from newsletter.models import ContentSource, current_week_of


class Command(BaseCommand):
    help = (
        "Poll active RSS ContentSources once and create draft ContentItems for "
        "review in the admin. For a continuously-running watcher that also "
        "handles plain (non-RSS) pages, see 'run_watch_bot' instead."
    )

    def handle(self, *args, **options):
        week_of = current_week_of()
        sources = ContentSource.objects.filter(
            active=True, source_type=ContentSource.SourceType.RSS
        ).select_related("state")
        total_created = 0

        for source in sources:
            created, error = process_rss_source(source, week_of)
            if error:
                self.stderr.write(self.style.WARNING(f"{source}: {error}"))
            elif created:
                self.stdout.write(f"{source}: {created} new draft item(s)")
            total_created += created

        self.stdout.write(self.style.SUCCESS(f"Done. {total_created} new draft content item(s) created."))
        self.stdout.write("Review and approve them in /admin/newsletter/contentitem/ before sending.")
