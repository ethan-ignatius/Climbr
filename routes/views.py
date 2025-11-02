from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import RouteForm
from .models import Route, RouteImage

import os
import re
import unicodedata

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Route

class MyRoutesView(LoginRequiredMixin, ListView):
    template_name = "routes/my_routes.html"
    context_object_name = "routes"
    login_url = "login"          # or set settings.LOGIN_URL
    redirect_field_name = "next" # preserves return path after login

    def get_queryset(self):
        """
        Returns all routes owned by the current user.
        Adjust the field name below if your owner field is not `author`.
        """
        user = self.request.user
        qs = Route.objects.all()

        # Try common owner fields intelligently to avoid FieldErrors.
        fields = {f.name: f for f in Route._meta.get_fields()}

        # author (FK or CharField)
        if "author" in fields:
            f = fields["author"]
            if getattr(f, "is_relation", False):
                return qs.filter(author=user).order_by("-id")
            else:
                return qs.filter(author__iexact=user.get_username()).order_by("-id")

        # owner (FK or CharField)
        if "owner" in fields:
            f = fields["owner"]
            if getattr(f, "is_relation", False):
                return qs.filter(owner=user).order_by("-id")
            else:
                return qs.filter(owner__iexact=user.get_username()).order_by("-id")

        # created_by (FK or CharField)
        if "created_by" in fields:
            f = fields["created_by"]
            if getattr(f, "is_relation", False):
                return qs.filter(created_by=user).order_by("-id")
            else:
                return qs.filter(created_by__iexact=user.get_username()).order_by("-id")

        # Fallback: nothing matched
        return qs.none()

def _slugify_simple(value: str, allow_unicode: bool = False) -> str:
    """
    Lightweight slugify: lowercase, spaces -> '-', remove anything not alnum, dash, or underscore.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[\s-]+", "-", value).strip("-")
    return value or "untitled"


def _normalized_ext(original_name: str) -> str:
    """
    Lowercase extension; fall back to .jpg if missing/unknown.
    """
    ext = os.path.splitext(original_name)[1].lower()
    if ext in {".jpg", ".jpeg"}: return ".jpg"
    if ext in {".png"}: return ".png"
    if ext in {".webp"}: return ".webp"
    if ext in {".gif"}: return ".gif"
    return ".jpg"


def route_list(request):
    routes = Route.objects.select_related("author").prefetch_related("images")
    return render(request, "routes/route_list.html", {"routes": routes})


def route_detail(request, pk: int):
    route = get_object_or_404(
        Route.objects.select_related("author").prefetch_related("images"),
        pk=pk
    )
    return render(request, "routes/route_detail.html", {"route": route})


@login_required
def route_create(request):
    if request.method == "POST":
        form = RouteForm(user=request.user, is_edit=False)  # Add is_edit=False
        if form.is_valid():
            files = form.cleaned_data.get("images") or []

            # Save route first (need author/title to name files)
            route = form.save(commit=False)
            route.author = request.user
            route.save()

            user_slug = _slugify_simple(request.user.username or "user")
            title_slug = _slugify_simple(route.title or "route")

            for idx, f in enumerate(files, start=1):
                ext = _normalized_ext(getattr(f, "name", "") or "")
                # NOTE: plain index (no zero padding)
                new_name = f"{user_slug}_{title_slug}_{idx}{ext}"
                f.name = new_name  # ensures storage uses this filename
                RouteImage.objects.create(route=route, image=f, order=idx)

            messages.success(request, "Route added successfully!")
            return redirect("routes:detail", pk=route.pk)
        # fall through
    else:
        form = RouteForm(user=request.user)

    # Get user's location from their profile if available
    user_location = None
    if hasattr(request.user, 'userprofile') and request.user.userprofile.latitude and request.user.userprofile.longitude:
        user_location = {
            'latitude': float(request.user.userprofile.latitude),
            'longitude': float(request.user.userprofile.longitude)
        }

    context = {
        "form": form,
        "user_location": user_location
    }
    
    return render(request, "routes/route_form.html", context)

@login_required
def route_edit(request, pk: int):
    """Edit an existing route (only by author)"""
    route = get_object_or_404(
        Route.objects.select_related("author").prefetch_related("images"),
        pk=pk
    )
    
    # Check if user is the author
    if route.author != request.user:
        messages.error(request, "You can only edit routes you created.")
        return redirect("routes:detail", pk=route.pk)
    
    if request.method == "POST":
        form = RouteForm(request.POST, request.FILES, instance=route, user=request.user, is_edit=True)  # Add is_edit=True

        if form.is_valid():
            # Get new images (if any)
            files = form.cleaned_data.get("images") or []
            
            # Save route updates
            route = form.save(commit=True)
            
            # Handle new images
            if files:
                # Delete old images and replace with new ones
                route.images.all().delete()
                
                user_slug = _slugify_simple(request.user.username or "user")
                title_slug = _slugify_simple(route.title or "route")
                
                for idx, f in enumerate(files, start=1):
                    ext = _normalized_ext(getattr(f, "name", "") or "")
                    new_name = f"{user_slug}_{title_slug}_{idx}{ext}"
                    f.name = new_name
                    RouteImage.objects.create(route=route, image=f, order=idx)
            
            messages.success(request, "Route updated successfully!")
            return redirect("routes:detail", pk=route.pk)
        # fall through to show form with errors
    else:
        form = RouteForm(instance=route, user=request.user, is_edit=True)  # Add is_edit=True

    # Get user's location from their profile if available
    user_location = None
    if hasattr(request.user, 'profile') and request.user.profile.latitude and request.user.profile.longitude:
        user_location = {
            'latitude': float(request.user.profile.latitude),
            'longitude': float(request.user.profile.longitude)
        }
    
    context = {
        "form": form,
        "user_location": user_location,
        "route": route,
        "is_edit": True
    }
    
    return render(request, "routes/route_form.html", context)