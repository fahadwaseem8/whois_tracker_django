from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tracker.api import api
from tracker import views as frontend_views

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # REST API
    path("api/v1/", api.urls),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="tracker/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Frontend
    path("", frontend_views.index, name="index"),
    path("dashboard/", frontend_views.dashboard, name="dashboard"),
    path("domains/<int:domain_id>/", frontend_views.domain_detail, name="domain_detail"),
]
