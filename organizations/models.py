from django.db import models


class Organization(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Tashkilot nomi"
    )

    inn = models.CharField(
        max_length=9,
        unique=True,
        verbose_name="Tashkilot INN raqami"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt"
    )

    class Meta:
        verbose_name = "Tashkilot"
        verbose_name_plural = "Tashkilotlar"
        ordering = ["name"]

    def __str__(self):
        return self.name





class Department(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="Tashkilot"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Bo‘lim nomi"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt"
    )

    class Meta:
        verbose_name = "Bo‘lim"
        verbose_name_plural = "Bo‘limlar"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_department_per_organization"
            )
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"