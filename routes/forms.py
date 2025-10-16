from django import forms
from django.core.exceptions import ValidationError
from .models import Route, RouteImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    """Accept multiple uploaded files (list) without raising 'No file was submitted'."""
    def to_python(self, data):
        if isinstance(data, (list, tuple)):
            return list(data)
        return super().to_python(data)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            data = list(data)
            if self.required and not data:
                raise ValidationError(
                    self.error_messages.get('required', 'This field is required.'),
                    code='required'
                )
            return data
        return super().clean(data, initial)


class RouteForm(forms.ModelForm):
    # Inject request.user via __init__ so we can check per-user uniqueness
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    # Title (clean in clean_title to avoid duplicates & trim)
    title = forms.CharField(
        max_length=150,
        required=True,
        label='Title',
        error_messages={'required': 'Please add a title.'}
    )

    # Difficulty: dropdown 1..10 with a blank first option
    difficulty = forms.TypedChoiceField(
        required=True,
        label='Difficulty',
        choices=[('', '— Select —')] + [(str(i), str(i)) for i in range(1, 11)],
        coerce=int,
        empty_value=None,
        widget=forms.Select(),
        error_messages={'required': 'Please select a difficulty.'}
    )

    video_url = forms.URLField(required=False, label="YouTube URL (optional)")

    # Float fields: allow any precision, only validate ranges
    latitude = forms.FloatField(
        required=False,
        label="Latitude",
        widget=forms.NumberInput(attrs={'step': 'any', 'inputmode': 'decimal'})
    )
    longitude = forms.FloatField(
        required=False,
        label="Longitude",
        widget=forms.NumberInput(attrs={'step': 'any', 'inputmode': 'decimal'})
    )
    location_name = forms.CharField(required=False, max_length=200, label="Location (text)")

    images = MultiFileField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True}),
        help_text="Upload 1 to 9 images."
    )

    class Meta:
        model = Route
        fields = [
            "title", "description", "difficulty",
            "location_name", "latitude", "longitude", "video_url"
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    # Trim and per-user uniqueness check (case-insensitive)
    def clean_title(self):
        v = (self.cleaned_data.get("title") or "").strip()
        if not v:
            raise forms.ValidationError("Please add a title.")
        # Need the current user to check duplicates
        if self.user and Route.objects.filter(
            author=self.user, title__iexact=v
        ).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("You already have a route with this title.")
        return v

    def clean(self):
        cleaned = super().clean()

        # Description required
        if not (cleaned.get("description") or "").strip():
            if "description" not in self.errors:
                self.add_error("description", "Please add a description.")

        # Latitude validation only (no decimal precision enforcement)
        lat = cleaned.get("latitude")
        if lat is not None:
            try:
                lat_f = float(lat)
            except Exception:
                self.add_error("latitude", "Invalid latitude. Must be between -90 and 90.")
            else:
                if not (-90.0 <= lat_f <= 90.0):
                    self.add_error("latitude", "Invalid latitude. Must be between -90 and 90.")

        # Longitude validation only (no decimal precision enforcement)
        lng = cleaned.get("longitude")
        if lng is not None:
            try:
                lng_f = float(lng)
            except Exception:
                self.add_error("longitude", "Invalid longitude. Must be between -180 and 180.")
            else:
                if not (-180.0 <= lng_f <= 180.0):
                    self.add_error("longitude", "Invalid longitude. Must be between -180 and 180.")

        # Require either name OR coords (not both)
        has_name = bool((cleaned.get("location_name") or "").strip())
        has_coords = (cleaned.get("latitude") is not None and cleaned.get("longitude") is not None)

        if not (has_name or has_coords):
            raise ValidationError("<strong>Location</strong>: choose on the map (lat/lng) or enter a location name.")
        if has_name and has_coords:
            cleaned["location_name"] = ""  # prefer coords if both provided

        # Enforce 1..9 images
        files = self.cleaned_data.get("images") or []
        if len(files) == 0:
            self.add_error("images", "Please upload between 1 to 9 images.")
        elif len(files) > 9:
            self.add_error("images", "Too many images selected. Please select at most 9.")

        return cleaned

    def clean_video_url(self):
        url = (self.cleaned_data.get("video_url") or "").strip()
        if not url:
            return url
        if "youtube.com" not in url and "youtu.be" not in url:
            raise forms.ValidationError("Please provide a YouTube URL.")
        return url
