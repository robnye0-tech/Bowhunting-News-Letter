from django import forms
from django.conf import settings

from .models import State


class SignupForm(forms.Form):
    email = forms.EmailField()
    states = forms.ModelMultipleChoiceField(
        queryset=State.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_states(self):
        states = self.cleaned_data["states"]
        if states.count() < 1:
            raise forms.ValidationError("Pick at least one state.")
        if states.count() > settings.MAX_STATES_PER_SUBSCRIBER:
            raise forms.ValidationError(
                f"Pick at most {settings.MAX_STATES_PER_SUBSCRIBER} states."
            )
        return states
