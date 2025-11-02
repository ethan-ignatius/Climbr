from django.shortcuts import render
from django.db.models import Q
from routes.models import Route

def home(request):
    # Include routes that already have coordinates OR at least have a location string
    routes_qs = (
        Route.objects
        .filter(
            Q(latitude__isnull=False, longitude__isnull=False) |
            (Q(location_name__isnull=False) & ~Q(location_name__exact=""))
        )
        .select_related("author")
    )

    # Serialize what the template expects
    routes_data = [{
        "pk": r.pk,
        "title": r.title,
        "description": r.description,
        "difficulty": r.difficulty,
        "author": r.author.get_username(),
        "location_name": r.location_name or "",
        "latitude": float(r.latitude) if r.latitude is not None else None,
        "longitude": float(r.longitude) if r.longitude is not None else None,
    } for r in routes_qs]

    # (optional) user location if you have it
    user_location = None
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        p = request.user.profile
        if getattr(p, "latitude", None) is not None and getattr(p, "longitude", None) is not None:
            user_location = {
                "latitude": float(p.latitude),
                "longitude": float(p.longitude),
                "location_name": getattr(p, "location_name", None),
            }

    return render(request, "home.html", {
        "routes": routes_data,
        "user_location": user_location,
    })
