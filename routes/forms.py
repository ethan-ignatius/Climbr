from django import forms
from .models import Route

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ["title", "description", "difficulty", "picture", "video_url"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_video_url(self):
        url = self.cleaned_data.get("video_url", "").strip()
        if not url:
            return url
        # require YouTube
        if "youtube.com" not in url and "youtu.be" not in url:
            raise forms.ValidationError("Please provide a YouTube URL.")
        return url
