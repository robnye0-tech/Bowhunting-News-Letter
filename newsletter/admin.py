from django.contrib import admin

from .models import ContentItem, ContentSource, NewsletterIssue, Product, State, Subscriber, Subscription


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "state_list", "created_at")
    list_filter = ("status",)
    search_fields = ("email",)
    inlines = [SubscriptionInline]
    readonly_fields = ("confirm_token", "unsubscribe_token", "created_at", "updated_at")

    def state_list(self, obj):
        return ", ".join(s.code for s in obj.states.all())

    state_list.short_description = "States"


@admin.register(ContentSource)
class ContentSourceAdmin(admin.ModelAdmin):
    list_display = ("label", "state", "url", "source_type", "active")
    list_filter = ("state", "active", "source_type")
    search_fields = ("label", "url")


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("title", "state", "category", "status", "week_of", "published_at")
    list_filter = ("status", "category", "state", "week_of")
    search_fields = ("title", "summary", "url")
    date_hierarchy = "week_of"
    actions = ["approve_items", "reject_items"]
    fields = (
        "state",
        "source",
        "category",
        "status",
        "title",
        "url",
        "summary",
        "published_at",
        "week_of",
    )

    @admin.action(description="Approve selected items for send")
    def approve_items(self, request, queryset):
        updated = queryset.update(status=ContentItem.Status.APPROVED)
        self.message_user(request, f"{updated} item(s) approved.")

    @admin.action(description="Reject selected items")
    def reject_items(self, request, queryset):
        updated = queryset.update(status=ContentItem.Status.REJECTED)
        self.message_user(request, f"{updated} item(s) rejected.")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "week_of", "url")
    list_filter = ("state", "week_of")
    search_fields = ("name", "description")
    date_hierarchy = "week_of"


@admin.register(NewsletterIssue)
class NewsletterIssueAdmin(admin.ModelAdmin):
    list_display = ("state", "week_of", "status", "sent_at", "recipient_count")
    list_filter = ("status", "state")
    date_hierarchy = "week_of"
    readonly_fields = ("sent_at", "recipient_count")
