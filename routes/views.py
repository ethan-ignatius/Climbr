from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .forms import RouteForm
from .models import Route, RouteImage, Favorite, Vote

import os
import re
import math
import requests
import unicodedata
from functools import lru_cache

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Route

class MyRoutesView(LoginRequiredMixin, ListView):
    template_name = "routes/my_routes.html"
    context_object_name = "routes"
    login_url = "login"
    redirect_field_name = "next"

    def get_queryset(self):
        """
        Returns all routes owned by the current user.
        Adjust the field name below if your owner field is not `author`.
        """
        user = self.request.user
        qs = Route.objects.all()

        fields = {f.name: f for f in Route._meta.get_fields()}

        if "author" in fields:
            f = fields["author"]
            if getattr(f, "is_relation", False):
                return qs.filter(author=user).order_by("-id")
            else:
                return qs.filter(author__iexact=user.get_username()).order_by("-id")

        if "owner" in fields:
            f = fields["owner"]
            if getattr(f, "is_relation", False):
                return qs.filter(owner=user).order_by("-id")
            else:
                return qs.filter(owner__iexact=user.get_username()).order_by("-id")

        if "created_by" in fields:
            f = fields["created_by"]
            if getattr(f, "is_relation", False):
                return qs.filter(created_by=user).order_by("-id")
            else:
                return qs.filter(created_by__iexact=user.get_username()).order_by("-id")

        return qs.none()


class MyFavoriteRoutesView(LoginRequiredMixin, ListView):
    """
    Shows all routes that the current user has favorited.
    """
    template_name = "routes/my_favorite_routes.html"
    context_object_name = "routes"
    login_url = "login"
    redirect_field_name = "next"

    def get_queryset(self):
        user = self.request.user
        return (
            Route.objects
            .filter(favorites__user=user)
            .select_related("author")
            .prefetch_related("images")  # keep similar to route_list
            .distinct()
            .order_by("-id")
        )

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
        Route.objects.select_related("author").prefetch_related("images", "favorites", "votes"),
        pk=pk
    )
    
    # Get user's interaction status with this route
    user_data = {
        'is_favorited': route.is_favorited_by(request.user) if request.user.is_authenticated else False,
        'user_vote': route.get_user_vote(request.user) if request.user.is_authenticated else None,
    }
    
    return render(request, "routes/route_detail.html", {
        "route": route,
        "user_data": user_data
    })


@login_required
def route_create(request):
    if request.method == "POST":
        # Include POST data and files
        form = RouteForm(request.POST, request.FILES, user=request.user, is_edit=False)

        if form.is_valid():
            files = form.cleaned_data.get("images") or []

            # Save route instance
            route = form.save(commit=False)
            route.author = request.user
            route.save()

            user_slug = _slugify_simple(request.user.username or "user")
            title_slug = _slugify_simple(route.title or "route")

            for idx, f in enumerate(files, start=1):
                ext = _normalized_ext(getattr(f, "name", "") or "")
                new_name = f"{user_slug}_{title_slug}_{idx}{ext}"
                f.name = new_name
                RouteImage.objects.create(route=route, image=f, order=idx)

            messages.success(request, "Route added successfully!")
            return redirect("routes:detail", pk=route.pk)
        # fall through to show form with errors
    else:
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")

        initial = {}
        if lat and lng:
            initial["latitude"] = lat
            initial["longitude"] = lng

        form = RouteForm(user=request.user, initial=initial)

    context = {"form": form}
    return render(request, "routes/route_form.html", context)


@login_required
def route_delete(request, pk: int):
    """Deletes an existing route (only by author)"""
    route = get_object_or_404(
        Route.objects.select_related("author").prefetch_related("images"),
        pk=pk
    )

    # Checks if user is the author
    if route.author != request.user:
        messages.error(request, "You can only delete routes you created.")
        return redirect("routes:detail", pk=route.pk)
    
    if request.method == "POST":
        route.delete()
        messages.success(request, "Route deleted sucessfully.")
        return redirect("routes:my_routes")
    
    return redirect("routes:detail", pk=route.pk)



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

@lru_cache(maxsize=512)
def _geocode_first(location_text: str):
    """
    Return (lat, lon) using the first result from Nominatim for the given text.
    Cached in-process to avoid repeat lookups.
    """
    if not location_text:
        return None

    base = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_text, "format": "jsonv2", "limit": 1}
    headers = {"User-Agent": "ClimbApp/1.0 (contact@climbapp.local)"}

    try:
        if requests:
            resp = requests.get(base, params=params, headers=headers, timeout=6)
            resp.raise_for_status()
            data = resp.json()
        else:
            import urllib.parse, urllib.request, json as _json
            url = base + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as f:
                data = _json.loads(f.read().decode("utf-8"))
        if isinstance(data, list) and data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        # Swallow errors and just treat it as ungeocodable
        return None

    return None


def route_search(request):
    """
    Public search by difficulty + distance. If a route lacks coordinates but has
    a location text, we geocode it using the first map result (Nominatim) and
    use that to compute distance.
    """
    # ---- input parsing
    def as_int(val, default, lo, hi):
        try:
            v = int(val)
            return max(lo, min(hi, v))
        except (TypeError, ValueError):
            return default

    diff_min = as_int(request.GET.get("difficulty_min"), 1, 1, 10)
    diff_max = as_int(request.GET.get("difficulty_max"), 10, 1, 10)
    if diff_min > diff_max:
        diff_min, diff_max = diff_max, diff_min

    try:
        radius = float(request.GET.get("radius", 25))
    except (TypeError, ValueError):
        radius = 25.0

    def as_float(k):
        v = request.GET.get(k)
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    lat = as_float("lat")
    lng = as_float("lng")

    # Optional fallback to saved profile location if user is logged in
    profile_loc = None
    user = getattr(request, "user", None)
    if (lat is None or lng is None) and getattr(user, "is_authenticated", False) and hasattr(user, "profile"):
        p = user.profile
        if getattr(p, "latitude", None) is not None and getattr(p, "longitude", None) is not None:
            profile_loc = (float(p.latitude), float(p.longitude))
            if lat is None: lat = profile_loc[0]
            if lng is None: lng = profile_loc[1]

    # ---- query
    from .models import Route
    qs = Route.objects.filter(difficulty__gte=diff_min, difficulty__lte=diff_max)
    routes_all = list(qs.select_related("author").prefetch_related("images"))

    # ---- helpers
    def haversine_miles(lat1, lon1, lat2, lon2):
        R = 3958.7613  # miles
        phi1 = math.radians(lat1); phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_location_text(route):
        # Try a few common field names; adjust if your model uses a different name
        for field in ("location_name", "location", "address", "place"):
            val = getattr(route, field, None)
            if val:
                return str(val)
        return None

    # ---- distance filtering
    active_location = None
    within = []   # routes with known/derived coordinates and within radius
    unknown = []  # couldn’t geocode (still included at the end)

    if lat is not None and lng is not None:
        active_location = {"latitude": float(lat), "longitude": float(lng)}

        for r in routes_all:
            rlat = getattr(r, "latitude", None)
            rlng = getattr(r, "longitude", None)

            if rlat is None or rlng is None:
                # Try to geocode text-only location
                loc_text = get_location_text(r)
                coords = _geocode_first(loc_text) if loc_text else None
                if coords:
                    rlat, rlng = coords  # ephemeral; not persisted

            if rlat is not None and rlng is not None:
                d = haversine_miles(float(rlat), float(rlng), float(lat), float(lng))
                setattr(r, "distance_miles", d)
                if d <= radius:
                    within.append(r)
            else:
                unknown.append(r)

        within.sort(key=lambda x: getattr(x, "distance_miles", 1e9))
        filtered = within + unknown
    else:
        # No user location: just difficulty filter (no distance)
        filtered = routes_all
        within = filtered
        unknown = []

    context = {
        "routes": filtered,
        "filters": {"difficulty_min": diff_min, "difficulty_max": diff_max, "radius": radius},
        "active_location": active_location,
        "used_profile_fallback": profile_loc is not None,
        "results_count": len(filtered),
        "within_count": len(within),
        "unknown_count": len(unknown),
    }
    return render(request, "routes/route_search.html", context)


@login_required
@require_POST
def toggle_favorite(request, pk):
    """Toggle favorite status for a route via AJAX"""
    try:
        route = get_object_or_404(Route, pk=pk)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, 
            route=route
        )
        
        if not created:
            # Favorite already existed, so remove it
            favorite.delete()
            is_favorited = False
        else:
            # New favorite was created
            is_favorited = True
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'favorites_count': route.favorites.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def vote_route(request, pk):
    """Handle upvote/downvote for a route via AJAX"""
    try:
        route = get_object_or_404(Route, pk=pk)
        is_upvote = request.POST.get('is_upvote') == 'true'
        
        # Get or create the vote
        vote, created = Vote.objects.get_or_create(
            user=request.user,
            route=route,
            defaults={'is_upvote': is_upvote}
        )
        
        if not created:
            if vote.is_upvote == is_upvote:
                # User clicked the same vote type - remove the vote
                vote.delete()
                user_vote = None
            else:
                # User switched vote type
                vote.is_upvote = is_upvote
                vote.save()
                user_vote = is_upvote
        else:
            # New vote created
            user_vote = is_upvote
        
        return JsonResponse({
            'success': True,
            'user_vote': user_vote,  # None, True (upvote), or False (downvote)
            'upvotes_count': route.get_upvotes_count(),
            'downvotes_count': route.get_downvotes_count(),
            'net_votes': route.get_net_votes()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)