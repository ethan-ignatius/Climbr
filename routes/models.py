from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.db import models
from django.db.models.functions import Lower  # NEW
from urllib.parse import quote_plus


class Route(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    # ---- Location ----
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location_name = models.CharField(
        max_length=200, blank=True, help_text="e.g., Red River Gorge, KY"
    )

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
        ordering = [Lower("title"), "id"]

    def __str__(self):
        return f"{self.title} (#{self.pk})"

    # ---- Convenience getters used by templates ----
    def has_coords(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def get_upvotes_count(self):
        """Get the number of upvotes for this route"""
        return self.votes.filter(is_upvote=True).count()
    
    def get_downvotes_count(self):
        """Get the number of downvotes for this route"""
        return self.votes.filter(is_upvote=False).count()
    
    def get_net_votes(self):
        """Get the net vote count (upvotes - downvotes)"""
        return self.get_upvotes_count() - self.get_downvotes_count()
    
    def get_user_vote(self, user):
        """Get the current user's vote on this route (None, True for upvote, False for downvote)"""
        if not user.is_authenticated:
            return None
        try:
            vote = self.votes.get(user=user)
            return vote.is_upvote
        except Vote.DoesNotExist:
            return None
    
    def is_favorited_by(self, user):
        """Check if this route is favorited by the given user"""
        if not user.is_authenticated:
            return False
        return self.favorites.filter(user=user).exists()

    def youtube_id(self) -> str | None:
        """Extract the YouTube video id from watch / youtu.be / embed / shorts / live / mobile URLs."""
        if not getattr(self, "video_url", None):
            return None
        url = (self.video_url or "").strip()
        url = url.replace("m.youtube.com", "www.youtube.com")

        import re as _re
        patterns = [
            r"youtube\.com/watch\?[^#]*v=([A-Za-z0-9_-]{6,})",
            r"youtu\.be/([A-Za-z0-9_-]{6,})",
            r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
            r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})",
            r"youtube\.com/live/([A-Za-z0-9_-]{6,})",
        ]
        for pat in patterns:
            m = _re.search(pat, url)
            if m:
                return m.group(1)
        return None

    def youtube_embed_src(self) -> str | None:
        """Return an embeddable YouTube URL for many URL shapes."""
        vid = self.youtube_id()
        if not vid:
            return None
        # Standard embed domain with safe params
        params = "rel=0&modestbranding=1&playsinline=1&iv_load_policy=3"
        return f"https://www.youtube.com/embed/{vid}?{params}"

    def map_embed_src(self) -> str | None:
        """
        Prefer precise lat/long; otherwise search by name.
        Returns an embeddable Google Maps URL suitable for an <iframe>.
        """
        if self.has_coords():
            try:
                lat = float(self.latitude)
                lng = float(self.longitude)
            except (TypeError, ValueError):
                lat = lng = None
            if (
                lat is not None
                and -90.0 <= lat <= 90.0
                and lng is not None
                and -180.0 <= lng <= 180.0
            ):
                return f"https://www.google.com/maps?q={lat},{lng}&z=14&output=embed"

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


class Favorite(models.Model):
    """Model to track users' favorite routes"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="favorite_routes"
    )
    route = models.ForeignKey(
        Route, 
        on_delete=models.CASCADE, 
        related_name="favorites"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'route')  # Prevent duplicate favorites
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favorites {self.route.title}"


class Vote(models.Model):
    """Model to track user votes (upvotes/downvotes) on routes"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="route_votes"
    )
    route = models.ForeignKey(
        Route, 
        on_delete=models.CASCADE, 
        related_name="votes"
    )
    is_upvote = models.BooleanField()  # True for upvote, False for downvote
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'route')  # One vote per user per route
        ordering = ['-updated_at']

    def __str__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"{self.user.username} {vote_type}s {self.route.title}"
