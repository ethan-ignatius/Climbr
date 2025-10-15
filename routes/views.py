from django.shortcuts import get_object_or_404, render
from .models import Route

def route_list(request):
    routes = Route.objects.select_related("author").prefetch_related("images")
    return render(request, "routes/route_list.html", {"routes": routes})

def route_detail(request, pk: int):
    route = get_object_or_404(Route.objects.select_related("author").prefetch_related("images"), pk=pk)
    return render(request, "routes/route_detail.html", {"route": route})
