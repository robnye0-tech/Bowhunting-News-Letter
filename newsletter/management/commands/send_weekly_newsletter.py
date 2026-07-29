from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse

from newsletter.emails import send_email
from newsletter.models import ContentItem, NewsletterIssue, Product, State, Subscriber, current_week_of

SECTIONS = [
    (ContentItem.Category.LAW_CHANGE, "Law Changes"),
    (ContentItem.Category.PROPOSED_LAW, "Proposed Law Changes"),
    (ContentItem.Category.PUBLIC_LAND, "Public Land Updates"),
    (ContentItem.Category.EHD_REPORT, "EHD Reports"),
    (ContentItem.Category.GENERAL, "Other News"),
]


class Command(BaseCommand):
    help = (
        "Compile and send this week's newsletter for each state that has approved "
        "content or products, to that state's confirmed subscribers. Safe to re-run: "
        "states already marked SENT for the current week are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Build issues and print recipient counts without sending or marking as sent.",
        )

    def handle(self, *args, **options):
        week_of = current_week_of()
        dry_run = options["dry_run"]

        for state in State.objects.all():
            issue, _ = NewsletterIssue.objects.get_or_create(state=state, week_of=week_of)
            if issue.status == NewsletterIssue.Status.SENT:
                continue

            items = ContentItem.objects.filter(
                state=state, week_of=week_of, status=ContentItem.Status.APPROVED
            )
            products = Product.objects.filter(state=state, week_of=week_of)

            if not items.exists() and not products.exists():
                continue

            sections = [
                {"label": label, "items": list(items.filter(category=category))}
                for category, label in SECTIONS
            ]

            subscribers = Subscriber.objects.filter(
                status=Subscriber.Status.CONFIRMED, states=state
            ).distinct()

            if not subscribers.exists():
                self.stdout.write(f"{state.name}: content ready but no confirmed subscribers, skipping send.")
                continue

            if dry_run:
                self.stdout.write(
                    f"[dry-run] {state.name}: would send to {subscribers.count()} subscriber(s)."
                )
                continue

            sent_count = 0
            for subscriber in subscribers:
                unsubscribe_url = f"{settings.SITE_BASE_URL}{reverse('newsletter:unsubscribe', args=[subscriber.unsubscribe_token])}"
                html = render_to_string(
                    "newsletter/emails/weekly_digest.html",
                    {
                        "state": state,
                        "week_of": week_of,
                        "sections": sections,
                        "products": products,
                        "unsubscribe_url": unsubscribe_url,
                    },
                )
                subject = f"Broadhead Brief — {state.name} — Week of {week_of.strftime('%B %d, %Y')}"
                send_email(subscriber.email, subject, html)
                sent_count += 1

            issue.status = NewsletterIssue.Status.SENT
            issue.sent_at = self._now()
            issue.recipient_count = sent_count
            issue.save()

            self.stdout.write(self.style.SUCCESS(f"{state.name}: sent to {sent_count} subscriber(s)."))

    @staticmethod
    def _now():
        from django.utils import timezone

        return timezone.now()
