from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    location_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your location (optional)',
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "location_name", "latitude", "longitude")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # The profile is created by the signal, so we just update it
            profile = user.profile
            profile.latitude = self.cleaned_data.get('latitude')
            profile.longitude = self.cleaned_data.get('longitude')
            profile.location_name = self.cleaned_data.get('location_name', '')
            profile.save()
        return user
