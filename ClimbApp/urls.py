from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),

    # Auth
    path("accounts/login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(next_page="home"), name="logout"),
    path("accounts/", include("accounts.urls", namespace="accounts")),

    # Routes feature
    path("routes/", include("routes.urls", namespace="routes")),
]

# Dev media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
