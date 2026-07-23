from django.contrib import admin
from .models import TrackedDomain, WhoisSnapshot

# Register your models here.

@admin.register(TrackedDomain)
class TrackedDomainAdmin(admin.ModelAdmin):
    list_display = ("domain_name", "user", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("domain_name", "user__username")

@admin.register(WhoisSnapshot)
class WhoisSnapshotAdmin(admin.ModelAdmin):
    list_display = ("domain", "payload_hash_short", "checked_at")
    list_filter = ("checked_at",)
    search_fields = ("domain__domain_name", "payload_hash")

    def payload_hash_short(self, obj):
        return obj.payload_hash[:12]
    payload_hash_short.short_description = "Hash"
    