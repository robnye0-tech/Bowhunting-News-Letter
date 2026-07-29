from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/pending/", views.signup_pending, name="signup_pending"),
    path("confirm/<uuid:token>/", views.confirm, name="confirm"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
]
