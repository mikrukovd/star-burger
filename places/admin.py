from django.contrib import admin
from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ["address", "lon", "lat", "updated_at"]
    readonly_fields = ["updated_at"]
    search_fields = ["address"]
