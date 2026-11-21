from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("login/", views.SignInView.as_view(), name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.profile, name="profile"),
]
