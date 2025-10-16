from django.urls import path
from . import views

app_name = "routes"

urlpatterns = [
    path("add/", views.route_create, name="add"),   # NEW
    path("", views.route_list, name="list"),
    path("<int:pk>/", views.route_detail, name="detail"),
]
