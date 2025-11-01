from django.shortcuts import render
from routes.models import Route

def home(request):
    # Get all routes that have coordinates for the map
    routes_with_coords = Route.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).select_related('author')
    
    return render(request, "home.html", {"routes": routes_with_coords})
