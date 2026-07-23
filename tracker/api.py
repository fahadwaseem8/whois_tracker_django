from typing import List
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.security import django_auth
from .models import TrackedDomain
from .services import process_domain_check

api = NinjaAPI(title="WHOIS Tracker API", version="1.0.0", auth=django_auth)


# Pydantic-style Data Schemas
class DomainIn(Schema):
    domain_name: str


class DomainOut(Schema):
    id: int
    domain_name: str
    is_active: bool
    created_at: str


class CheckResultOut(Schema):
    domain: str
    changed: bool


@api.post("/domains/", response=DomainOut)
def create_tracked_domain(request, payload: DomainIn):
    domain_clean = payload.domain_name.lower().strip()
    domain, _ = TrackedDomain.objects.get_or_create(
        user=request.user,
        domain_name=domain_clean
    )
    return domain


@api.get("/domains/", response=List[DomainOut])
def list_user_domains(request):
    return TrackedDomain.objects.filter(user=request.user)


@api.post("/domains/{domain_id}/check", response=CheckResultOut)
def trigger_manual_lookup(request, domain_id: int):
    domain = get_object_or_404(TrackedDomain, id=domain_id, user=request.user)
    changed = process_domain_check(domain.id)
    return {"domain": domain.domain_name, "changed": changed}
