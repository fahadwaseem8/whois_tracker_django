from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TrackedDomain(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tracked_domains")
    domain_name = models.CharField(max_length=255, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "domain_name")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.domain_name} ({self.user.username})"

class WhoisSnapshot(models.Model):
    domain = models.ForeignKey(TrackedDomain, on_delete=models.CASCADE, related_name="snapshots")
    payload_hash = models.CharField(max_length=64, db_index=True)
    raw_json = models.TextField()
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.domain.domain_name} - {self.payload_hash[:8]} ({self.checked_at.strftime('%Y-%m-%d')})"
        