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


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['experience_level', 'bio', 'email', 'location_name', 'latitude', 'longitude']
        widgets = {
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself and your climbing experience...'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Boulder, CO'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
