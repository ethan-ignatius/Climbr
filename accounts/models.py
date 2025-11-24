from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='beginner',
        help_text="Your climbing experience level"
    )
    bio = models.TextField(
        blank=True,
        max_length=500,
        help_text="Tell us about yourself and your climbing experience"
    )
    email = models.EmailField(
        blank=True,
        help_text="Contact email"
    )
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., Boulder, CO"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_location(self) -> bool:
        return self.latitude is not None and self.longitude is not None


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new user is created."""
    if kwargs.get("raw", False):
        return
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the user is saved."""
    if kwargs.get("raw", False):
        return
    if hasattr(instance, 'profile'):
        instance.profile.save()
