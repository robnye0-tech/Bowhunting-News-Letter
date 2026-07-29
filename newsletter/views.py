from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .emails import send_email
from .forms import SignupForm
from .models import Subscriber, Subscription


def home(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            states = form.cleaned_data["states"]

            subscriber, _ = Subscriber.objects.get_or_create(email=email)
            if subscriber.status == Subscriber.Status.UNSUBSCRIBED:
                subscriber.status = Subscriber.Status.PENDING

            # Re-signing up replaces any previously selected states.
            Subscription.objects.filter(subscriber=subscriber).exclude(state__in=states).delete()
            for state in states:
                Subscription.objects.get_or_create(subscriber=subscriber, state=state)

            if subscriber.status != Subscriber.Status.CONFIRMED:
                subscriber.status = Subscriber.Status.PENDING
                subscriber.save()
                _send_confirmation_email(request, subscriber)
            else:
                subscriber.save()

            return redirect("newsletter:signup_pending")
    else:
        form = SignupForm()

    return render(request, "newsletter/home.html", {"form": form})


def _send_confirmation_email(request, subscriber):
    confirm_url = request.build_absolute_uri(
        reverse("newsletter:confirm", args=[subscriber.confirm_token])
    )
    html = render_to_string(
        "newsletter/emails/confirm_email.html",
        {"confirm_url": confirm_url},
    )
    send_email(subscriber.email, "Confirm your Bowhunting Newsletter subscription", html)


def signup_pending(request):
    return render(request, "newsletter/signup_pending.html")


def confirm(request, token):
    subscriber = get_object_or_404(Subscriber, confirm_token=token)
    subscriber.status = Subscriber.Status.CONFIRMED
    subscriber.save()
    return render(request, "newsletter/confirmed.html", {"subscriber": subscriber})


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, unsubscribe_token=token)
    subscriber.status = Subscriber.Status.UNSUBSCRIBED
    subscriber.save()
    return render(request, "newsletter/unsubscribed.html", {"subscriber": subscriber})
