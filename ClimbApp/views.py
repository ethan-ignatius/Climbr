import json
from django.shortcuts import render
from routes.models import Route

def home(request):
    # Get all routes that have coordinates for the map
    routes_with_coords = Route.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).select_related('author')
    
    # Get user location if authenticated and has profile with location
    user_location = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.has_location():
            user_location = json.dumps({
                'latitude': profile.latitude,
                'longitude': profile.longitude,
                'location_name': profile.location_name
            })
    
    return render(request, "home.html", {
        "routes": routes_with_coords,
        "user_location": user_location
    })
