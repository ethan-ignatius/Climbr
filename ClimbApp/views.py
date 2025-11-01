import json
from django.shortcuts import render
from routes.models import Route

def home(request):
    # Get all routes that have coordinates for the map
    routes_with_coords = Route.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).select_related('author')
    
    # Convert routes to serializable format
    routes_data = []
    for route in routes_with_coords:
        routes_data.append({
            'pk': route.pk,
            'title': route.title,
            'description': route.description,
            'difficulty': route.difficulty,
            'author': route.author.username,
            'location_name': route.location_name or '',
            'latitude': float(route.latitude) if route.latitude else 0,
            'longitude': float(route.longitude) if route.longitude else 0,
        })
    
    # Get user location if authenticated and has profile with location
    user_location = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.has_location():
            user_location = {
                'latitude': float(profile.latitude),
                'longitude': float(profile.longitude),
                'location_name': profile.location_name
            }
    
    return render(request, "home.html", {
        "routes": routes_data,
        "user_location": user_location
    })
