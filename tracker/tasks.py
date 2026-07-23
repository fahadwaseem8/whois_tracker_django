from django_q.tasks import async_task
from .models import TrackedDomain
from .services import process_domain_check

def dispatch_daily_whois_checks():
    """Cron job entrypoint: pushes individual domain lookups to the worker queue."""
    active_domains = TrackedDomain.objects.filter(is_active=True).values_list("id", flat=True)
    for domain_id in active_domains:
        async_task(process_domain_check, domain_id)
        