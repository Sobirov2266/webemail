from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, DigitalKey


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User

    list_display = (
        "username",
        "first_name",
        "last_name",
        "department",
        "position",
        "role",
        "is_active",
    )

    list_filter = (
        "role",
        "is_active",
        "department",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "department__name",
        "department__organization__name",
    )

    ordering = (
        "last_name",
        "first_name",
    )

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": (
                "username",
                "password",
            )
        }),
        ("Xodim ma'lumotlari", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "department",
                "position",
            )
        }),
        ("Tizim", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
    )

    add_fieldsets = (
        ("Kirish ma'lumotlari", {
            "classes": ("wide",),
            "fields": (
                "username",
                "password1",
                "password2",
            ),
        }),
        ("Xodim ma'lumotlari", {
            "classes": ("wide",),
            "fields": (
                "first_name",
                "last_name",
                "email",
                "department",
                "position",
                "role",
            ),
        }),
    )


@admin.register(DigitalKey)
class DigitalKeyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "algorithm",
        "fingerprint",
        "is_active",
        "created_at",
        "expires_at",
    )

    list_filter = (
        "algorithm",
        "is_active",
        "purpose",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "fingerprint",
        "key_id",
    )

    readonly_fields = (
        "key_id",
        "created_at",
        "revoked_at",
    )