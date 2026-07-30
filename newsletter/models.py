import uuid

from django.db import models
from django.utils import timezone


def current_week_of():
    """Return the Monday (as a date) of the current local week."""
    today = timezone.localdate()
    return today - timezone.timedelta(days=today.weekday())


class State(models.Model):
    code = models.CharField(max_length=2, unique=True, help_text="Two-letter postal code, e.g. TX")
    name = models.CharField(max_length=50, unique=True)
    is_launched = models.BooleanField(
        default=False,
        help_text="Only launched states are offered on the public signup form.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subscriber(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    states = models.ManyToManyField(State, through="Subscription", related_name="subscribers")
    confirm_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_confirmed(self):
        return self.status == self.Status.CONFIRMED


class Subscription(models.Model):
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("subscriber", "state")

    def __str__(self):
        return f"{self.subscriber.email} → {self.state.code}"


class ContentSource(models.Model):
    """A feed to poll weekly for candidate newsletter content in a given state."""

    class SourceType(models.TextChoices):
        RSS = "rss", "RSS/Atom feed"
        PAGE = "page", "Plain page (watched for changes)"

    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="sources")
    label = models.CharField(max_length=200, help_text="e.g. 'Texas Parks & Wildlife News'")
    url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.RSS)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Used only for source_type=PAGE: lets the watch bot detect when a page's
    # text content has changed since it last checked, instead of re-flagging
    # an unchanged page every run.
    last_seen_hash = models.CharField(max_length=64, blank=True, default="")
    last_checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["state__name", "label"]

    def __str__(self):
        return f"{self.state.code}: {self.label}"


class ContentItem(models.Model):
    class Category(models.TextChoices):
        LAW_CHANGE = "law_change", "Law change"
        PROPOSED_LAW = "proposed_law", "Proposed law change"
        PUBLIC_LAND = "public_land", "Public land update"
        EHD_REPORT = "ehd_report", "EHD report"
        GENERAL = "general", "General / uncategorized"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft (needs review)"
        APPROVED = "approved", "Approved for send"
        REJECTED = "rejected", "Rejected"

    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="content_items")
    source = models.ForeignKey(
        ContentSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=500)
    summary = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    week_of = models.DateField(default=current_week_of, help_text="Monday of the newsletter week this belongs to")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-week_of", "state__name", "category"]
        indexes = [models.Index(fields=["state", "week_of", "status"])]

    def __str__(self):
        return f"[{self.state.code}] {self.title}"


class Product(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500, help_text="Product or affiliate link")
    description = models.CharField(max_length=500, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    week_of = models.DateField(default=current_week_of)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-week_of", "state__name"]

    def __str__(self):
        return f"[{self.state.code}] {self.name}"


class NewsletterIssue(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"

    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="issues")
    week_of = models.DateField(default=current_week_of)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("state", "week_of")
        ordering = ["-week_of", "state__name"]

    def __str__(self):
        return f"{self.state.code} — week of {self.week_of} ({self.status})"
