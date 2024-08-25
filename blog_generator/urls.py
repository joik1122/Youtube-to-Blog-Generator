from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.user_login, name="index"),
    path("signup", views.user_signup, name="index"),
    path("logout", views.user_logout, name="index"),
]
