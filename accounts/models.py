import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
from django.db.models import Q


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username kiritilishi shart")

        user = self.model(
            username=username,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        user = self.create_user(
            username=username,
            password=password,
            **extra_fields
        )

        return user


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        USER = "USER", "Foydalanuvchi"

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Login"
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name="Ism"
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name="Familiya"
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Email"
    )

    department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.PROTECT,
        related_name="users",
        verbose_name="Bo‘lim",
        null=True,
        blank=True
    )

    position = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Lavozim"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name="Rol"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name="Admin panelga kirish"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt"
    )

    objects = UserManager()

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DigitalKey(models.Model):

    class Purpose(models.TextChoices):
        AUTHENTICATION = "AUTHENTICATION", "Tizimga kirish"

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="digital_keys",
        verbose_name="Xodim"
    )

    key_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Kalit ID"
    )

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
        default=Purpose.AUTHENTICATION,
        verbose_name="Maqsad"
    )

    algorithm = models.CharField(
        max_length=50,
        default="Ed25519",
        verbose_name="Algoritm"
    )

    public_key = models.TextField(
        verbose_name="Ochiq kalit"
    )

    fingerprint = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="Fingerprint"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Amal qilish muddati"
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bekor qilingan vaqt"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )

    class Meta:
        verbose_name = "ERI kaliti"
        verbose_name_plural = "ERI kalitlari"
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="one_active_key_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.algorithm}"
