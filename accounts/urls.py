from django.urls import path
from .views import SignUpView, ProfileView, ProfileEditView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("profile/<str:username>/", ProfileView.as_view(), name="user_profile"),
]
