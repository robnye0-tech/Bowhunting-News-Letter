import re
from datetime import datetime, timezone as dt_timezone

import feedparser
from django.core.management.base import BaseCommand

from newsletter.models import ContentItem, ContentSource, current_week_of

TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(raw: str) -> str:
    return TAG_RE.sub("", raw or "").strip()


class Command(BaseCommand):
    help = (
        "Poll active ContentSource feeds and create draft ContentItems for review "
        "in the admin. Run this early in the week, before send_weekly_newsletter."
    )

    def handle(self, *args, **options):
        week_of = current_week_of()
        sources = ContentSource.objects.filter(active=True).select_related("state")
        total_created = 0

        for source in sources:
            try:
                feed = feedparser.parse(source.url)
            except Exception as exc:  # feedparser rarely raises, but network libs can
                self.stderr.write(self.style.WARNING(f"Failed to fetch {source.url}: {exc}"))
                continue

            if feed.bozo and not feed.entries:
                self.stderr.write(
                    self.style.WARNING(f"Could not parse feed for source '{source.label}' ({source.url})")
                )
                continue

            created_for_source = 0
            for entry in feed.entries:
                link = getattr(entry, "link", "")
                title = getattr(entry, "title", "").strip()
                if not link or not title:
                    continue
                if ContentItem.objects.filter(state=source.state, url=link).exists():
                    continue

                published_at = None
                if getattr(entry, "published_parsed", None):
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=dt_timezone.utc)

                ContentItem.objects.create(
                    state=source.state,
                    source=source,
                    title=title,
                    url=link,
                    summary=strip_tags(getattr(entry, "summary", ""))[:2000],
                    published_at=published_at,
                    week_of=week_of,
                )
                created_for_source += 1

            if created_for_source:
                self.stdout.write(f"{source}: {created_for_source} new draft item(s)")
            total_created += created_for_source

        self.stdout.write(self.style.SUCCESS(f"Done. {total_created} new draft content item(s) created."))
        self.stdout.write("Review and approve them in /admin/newsletter/contentitem/ before sending.")
