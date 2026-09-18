from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import User, DigitalKey
from organizations.models import Organization, Department


def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")

        return render(
            request,
            "accounts/admin_login.html",
            {
                "error": "Login yoki parol noto‘g‘ri."
            }
        )

    return render(request, "accounts/admin_login.html")


@login_required(login_url="admin_login")
def admin_dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Bu sahifa faqat administrator uchun."
        )

    context = {
        "organization_count": Organization.objects.count(),
        "department_count": Department.objects.count(),
        "user_count": User.objects.filter(
            is_superuser=False
        ).count(),
        "digital_key_count": DigitalKey.objects.filter(
            is_active=True
        ).count(),
    }

    return render(
        request,
        "accounts/admin_dashboard.html",
        context
    )


@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


@login_required(login_url="admin_login")
def organization_list(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    organizations = Organization.objects.all()

    return render(
        request,
        "accounts/organization_list.html",
        {
            "organizations": organizations
        }
    )


@login_required(login_url="admin_login")
def organization_detail(request, organization_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    organization = get_object_or_404(
        Organization,
        id=organization_id
    )

    departments = organization.departments.all()

    return render(
        request,
        "accounts/organization_detail.html",
        {
            "organization": organization,
            "departments": departments,
        }
    )


@login_required(login_url="admin_login")
def organization_create(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        inn = request.POST.get("inn", "").strip()
        description = request.POST.get("description", "").strip()

        if name and inn:
            # INN validatsiyasi - 9 xonali raqam
            if not inn.isdigit() or len(inn) != 9:
                return render(
                    request,
                    "accounts/organization_form.html",
                    {
                        "error": "INN 9 xonali raqamdan iborat bo'lishi kerak"
                    }
                )

            organization = Organization.objects.create(
                name=name,
                inn=inn,
                description=description,
            )

            return redirect(
                "organization_detail",
                organization_id=organization.id
            )

    return render(
        request,
        "accounts/organization_form.html"
    )


@login_required(login_url="admin_login")
def department_create(request, organization_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    organization = get_object_or_404(
        Organization,
        id=organization_id
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            Department.objects.create(
                organization=organization,
                name=name,
                description=description,
            )

            return redirect(
                "organization_detail",
                organization_id=organization.id
            )

    return render(
        request,
        "accounts/department_form.html",
        {
            "organization": organization
        }
    )


@login_required(login_url="admin_login")
def department_detail(request, department_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    department = get_object_or_404(
        Department,
        id=department_id
    )

    users = department.users.filter(
        is_superuser=False
    )

    return render(
        request,
        "accounts/department_detail.html",
        {
            "department": department,
            "users": users,
        }
    )


@login_required(login_url="admin_login")
def user_create(request, department_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    department = get_object_or_404(
        Department,
        id=department_id
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        position = request.POST.get("position", "").strip()

        if username and first_name and last_name:
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                department=department,
                position=position,
                role=User.Role.USER,
                is_active=True,
                is_staff=False,
            )

            user.set_unusable_password()
            user.save()

            return redirect(
                "department_detail",
                department_id=department.id
            )

    return render(
        request,
        "accounts/user_form.html",
        {
            "department": department
        }
    )