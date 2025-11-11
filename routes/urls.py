from django.urls import path
from . import views
from .views import MyRoutesView

app_name = "routes"

urlpatterns = [
    path("search/", views.route_search, name="search"),

    path("add/", views.route_create, name="add"),
    path("<int:pk>/edit/", views.route_edit, name="edit"),
    path("<int:pk>/delete/", views.route_delete, name="delete"),
    path("", views.route_list, name="list"),
    path("<int:pk>/", views.route_detail, name="detail"),
    path("mine/", MyRoutesView.as_view(), name="my_routes"),
]
