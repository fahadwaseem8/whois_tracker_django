from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    """Root redirect: logged-in → dashboard, else → login."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "tracker/dashboard.html")


@login_required
def domain_detail(request, domain_id: int):
    return render(request, "tracker/domain_detail.html", {"domain_id": domain_id})
