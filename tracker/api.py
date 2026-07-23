from typing import List
from datetime import datetime
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.security import django_auth
from django_q.tasks import async_task
from .models import TrackedDomain, WhoisSnapshot
from .services import process_domain_check

api = NinjaAPI(title="WHOIS Tracker API", version="1.0.0", auth=django_auth)


# ──────────────────────────────────────────────
# Pydantic-style Data Schemas
# ──────────────────────────────────────────────

class DomainIn(Schema):
    domain_name: str


class DomainOut(Schema):
    id: int
    domain_name: str
    is_active: bool
    created_at: datetime
    snapshot_count: int = 0


class CheckResultOut(Schema):
    domain: str
    changed: bool


class SnapshotOut(Schema):
    id: int
    payload_hash: str
    checked_at: datetime
    raw_json: str


class MessageOut(Schema):
    detail: str


# ──────────────────────────────────────────────
# Domain Endpoints
# ──────────────────────────────────────────────

@api.post("/domains/", response=DomainOut)
def create_tracked_domain(request, payload: DomainIn):
    domain_clean = payload.domain_name.lower().strip()
    domain, created = TrackedDomain.objects.get_or_create(
        user=request.user,
        domain_name=domain_clean
    )
    if created:
        # Fire an immediate WHOIS check in the background worker
        async_task(process_domain_check, domain.id)
    domain.snapshot_count = domain.snapshots.count()
    return domain


@api.get("/domains/", response=List[DomainOut])
def list_user_domains(request):
    domains = TrackedDomain.objects.filter(user=request.user)
    result = []
    for d in domains:
        d.snapshot_count = d.snapshots.count()
        result.append(d)
    return result


@api.delete("/domains/{domain_id}/", response=MessageOut)
def delete_tracked_domain(request, domain_id: int):
    domain = get_object_or_404(TrackedDomain, id=domain_id, user=request.user)
    name = domain.domain_name
    domain.delete()
    return {"detail": f"{name} removed successfully."}


@api.post("/domains/{domain_id}/check", response=CheckResultOut)
def trigger_manual_lookup(request, domain_id: int):
    domain = get_object_or_404(TrackedDomain, id=domain_id, user=request.user)
    changed = process_domain_check(domain.id)
    return {"domain": domain.domain_name, "changed": changed}


# ──────────────────────────────────────────────
# Snapshot Endpoints
# ──────────────────────────────────────────────

@api.get("/domains/{domain_id}/snapshots/", response=List[SnapshotOut])
def list_snapshots(request, domain_id: int):
    domain = get_object_or_404(TrackedDomain, id=domain_id, user=request.user)
    return domain.snapshots.all()
