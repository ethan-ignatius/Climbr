from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.db import models
from urllib.parse import quote_plus

class Route(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])

    # ---- Location ----
    location_name = models.CharField(max_length=200, blank=True, help_text="e.g., Red River Gorge, KY")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Legacy single image (optional)
    picture = models.ImageField(upload_to="routes/pictures/", blank=True, null=True)

    # Video (YouTube link)
    video_url = models.URLField(
        blank=True,
        help_text="YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)",
        validators=[URLValidator()],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (D{self.difficulty})"

    def youtube_embed_src(self) -> str | None:
        """Return an embeddable YouTube URL if video_url is a youtube link."""
        if not self.video_url:
            return None
        url = self.video_url
        vid = None
        if "youtube.com/watch?v=" in url:
            vid = url.split("v=", 1)[1].split("&", 1)[0]
        elif "youtu.be/" in url:
            vid = url.split("youtu.be/", 1)[1].split("?", 1)[0]
        return f"https://www.youtube.com/embed/{vid}" if vid else None

    def has_coords(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def map_embed_src(self) -> str | None:
        """
        Prefer precise lat/long; otherwise search by name.
        Returns an embeddable Google Maps URL suitable for an <iframe>.
        """
        if self.has_coords():
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}&z=14&output=embed"
        if self.location_name:
            q = quote_plus(self.location_name.strip())
            return f"https://www.google.com/maps?q={q}&z=14&output=embed"
        return None


class RouteImage(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="routes/pictures/")
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.route.title} (#{self.pk})"
