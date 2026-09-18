from django.urls import path

from .views import (
    admin_login,
    admin_dashboard,
    admin_logout,
    organization_list,
    organization_detail,
    organization_create,
    department_create,
    department_detail,
    user_create,
)


urlpatterns = [
    path(
        "admin-login/",
        admin_login,
        name="admin_login"
    ),

    path(
        "admin-dashboard/",
        admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-logout/",
        admin_logout,
        name="admin_logout"
    ),

    path(
        "admin/organizations/",
        organization_list,
        name="organization_list"
    ),

    path(
        "admin/organizations/create/",
        organization_create,
        name="organization_create"
    ),

    path(
        "admin/organizations/<int:organization_id>/",
        organization_detail,
        name="organization_detail"
    ),

    path(
        "admin/organizations/<int:organization_id>/departments/create/",
        department_create,
        name="department_create"
    ),

    path(
        "admin/departments/<int:department_id>/",
        department_detail,
        name="department_detail"
    ),

    path(
        "admin/departments/<int:department_id>/users/create/",
        user_create,
        name="user_create"
    ),
]