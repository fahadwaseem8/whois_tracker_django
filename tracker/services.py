import hashlib
import json
import httpx
from .models import TrackedDomain, WhoisSnapshot

def fetch_rdap_payload(domain_name: str) -> tuple[str, str]:
    """Queries standardized RDAP JSON data and generates a SHA-256 hash."""
    url = f"https://rdap.org/domain/{domain_name}"
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Ensure consistent serialization for hashing
        raw_json = json.dumps(data, sort_keys=True)
        payload_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        return raw_json, payload_hash

def process_domain_check(domain_id: int) -> bool:
    """Executes a lookup and stores a new snapshot if the hash changed."""
    try:
        domain = TrackedDomain.objects.get(id=domain_id, is_active=True)
    except TrackedDomain.DoesNotExist:
        return False

    try:
        raw_json, new_hash = fetch_rdap_payload(domain.domain_name)
    except Exception as exc:
        # In production, log error to monitoring service (Sentry, Datadog)
        print(f"Lookup failed for {domain.domain_name}: {exc}")
        return False

    latest_snapshot = domain.snapshots.first()
    if latest_snapshot and latest_snapshot.payload_hash == new_hash:
        return False  # No change detected

    WhoisSnapshot.objects.create(
        domain=domain,
        payload_hash=new_hash,
        raw_json=raw_json
    )
    return True