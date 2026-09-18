from django.contrib import admin
from .models import Organization, Department


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "inn",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "inn",
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "organization",
    )

    search_fields = (
        "name",
        "organization__name",
    )