from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone

import base64
import hashlib

from .models import User, DigitalKey, LoginChallenge
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


@login_required(login_url="admin_login")
def user_detail(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    user = get_object_or_404(
        User,
        id=user_id,
        is_superuser=False
    )

    digital_key = user.digital_keys.filter(
        is_active=True
    ).first()

    return render(request, "accounts/user_detail.html", {
        "user_obj": user,
        "digital_key": digital_key,
    })


@login_required(login_url="admin_login")
def generate_digital_key(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method != "POST":
        return HttpResponseForbidden()

    user = get_object_or_404(
        User,
        id=user_id,
        is_superuser=False
    )

    # Agar eski faol kalit mavjud bo‘lsa, yangi kalit yaratmaymiz
    existing_key = user.digital_keys.filter(
        is_active=True
    ).first()

    if existing_key:
        return HttpResponse(
            "Bu xodim uchun faol ERI kaliti allaqachon mavjud.",
            status=400
        )

    # 1. Ed25519 private key yaratamiz
    private_key = ed25519.Ed25519PrivateKey.generate()

    # 2. Public key olamiz
    public_key = private_key.public_key()

    # 3. Public keyni raw bytes ko‘rinishida olamiz
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # 4. Fingerprint yaratamiz
    fingerprint = hashlib.sha256(
        public_key_bytes
    ).hexdigest()

    # 5. Public keyni PEM formatga o'tkazamiz
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    # 6. DB ga faqat PUBLIC KEY saqlanadi
    digital_key = DigitalKey.objects.create(
        user=user,
        algorithm="Ed25519",
        public_key=public_key_pem,
        fingerprint=fingerprint,
        is_active=True,
    )

    # 7. PRIVATE KEY ni PEM formatda tayyorlaymiz
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # 8. .key fayl tarkibi
    key_file_content = (
        "WEBEMAIL DEMO DIGITAL KEY\n"
        "================================\n"
        f"Key ID: {digital_key.key_id}\n"
        f"Username: {user.username}\n"
        f"Algorithm: Ed25519\n"
        f"Fingerprint: {fingerprint}\n"
        "================================\n"
        "PRIVATE KEY\n"
        "================================\n"
    ).encode("utf-8") + private_key_pem

    # 9. Private keyni browserga yuklab beramiz
    response = HttpResponse(
        key_file_content,
        content_type="application/octet-stream"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="webemail_{user.username}.key"'
    )

    return response


def user_login(request):
    return render(request, "accounts/user_login.html")


@csrf_exempt
def check_digital_key(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Faqat POST so‘rov qabul qilinadi."
            },
            status=405
        )

    key_id = request.POST.get("key_id", "").strip()

    if not key_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Key ID yuborilmadi."
            },
            status=400
        )

    try:
        digital_key = DigitalKey.objects.select_related(
            "user",
            "user__department",
            "user__department__organization"
        ).get(
            key_id=key_id,
            is_active=True
        )

    except DigitalKey.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "ERI kaliti topilmadi yoki faol emas."
            },
            status=404
        )

    user = digital_key.user

    return JsonResponse(
        {
            "success": True,
            "message": "ERI kaliti topildi.",
            "key_id": str(digital_key.key_id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "position": user.position,
            "department": user.department.name
            if user.department else "",
            "organization": user.department.organization.name
            if user.department else "",
        }
    )


@csrf_exempt
def create_login_challenge(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Faqat POST so‘rov qabul qilinadi."
            },
            status=405
        )

    key_id = request.POST.get("key_id", "").strip()

    if not key_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Key ID yuborilmadi."
            },
            status=400
        )

    try:
        digital_key = DigitalKey.objects.select_related(
            "user"
        ).get(
            key_id=key_id,
            is_active=True
        )

    except DigitalKey.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "ERI kaliti topilmadi yoki faol emas."
            },
            status=404
        )

    # Xodim faol bo‘lishi kerak
    if not digital_key.user.is_active:
        return JsonResponse(
            {
                "success": False,
                "message": "Xodim akkaunti faol emas."
            },
            status=403
        )

    # Eski ishlatilmagan challenge'larni bekor qilamiz
    LoginChallenge.objects.filter(
        digital_key=digital_key,
        used_at__isnull=True
    ).update(
        used_at=timezone.now()
    )

    # 5 daqiqalik yangi challenge
    challenge = LoginChallenge.objects.create(
        digital_key=digital_key,
        expires_at=timezone.now() + timezone.timedelta(minutes=5)
    )

    return JsonResponse(
        {
            "success": True,
            "challenge": challenge.challenge,
            "expires_in": 300
        }
    )


@csrf_exempt
def verify_login_signature(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Faqat POST so‘rov qabul qilinadi."
            },
            status=405
        )

    key_id = request.POST.get("key_id", "").strip()
    challenge_text = request.POST.get("challenge", "").strip()
    signature_base64 = request.POST.get("signature", "").strip()

    if not key_id or not challenge_text or not signature_base64:
        return JsonResponse(
            {
                "success": False,
                "message": "Kerakli ma'lumotlar to‘liq yuborilmadi."
            },
            status=400
        )

    try:
        digital_key = DigitalKey.objects.select_related(
            "user"
        ).get(
            key_id=key_id,
            is_active=True
        )

    except DigitalKey.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "ERI kaliti topilmadi."
            },
            status=404
        )

    try:
        login_challenge = LoginChallenge.objects.get(
            digital_key=digital_key,
            challenge=challenge_text,
            used_at__isnull=True
        )

    except LoginChallenge.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Challenge topilmadi yoki allaqachon ishlatilgan."
            },
            status=400
        )

    # Challenge muddati tugaganini tekshiramiz
    if not login_challenge.is_valid():
        return JsonResponse(
            {
                "success": False,
                "message": "Challenge muddati tugagan."
            },
            status=400
        )

    try:
        # Base64 signature'ni bytes'ga aylantiramiz
        signature = base64.b64decode(
            signature_base64,
            validate=True
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "message": "Signature formati noto‘g‘ri."
            },
            status=400
        )

    try:
        # PostgreSQL'dagi Public Key'ni o‘qiymiz
        public_key = serialization.load_pem_public_key(
            digital_key.public_key.encode("utf-8")
        )

        # Challenge'ni aynan browser imzolagan holatda tayyorlaymiz
        challenge_bytes = challenge_text.encode("utf-8")

        # ENG MUHIM QISM
        public_key.verify(
            signature,
            challenge_bytes
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "message": "❌ ERI imzosi noto‘g‘ri."
            },
            status=401
        )

    # Challenge endi qayta ishlatilmasligi uchun belgilaymiz
    login_challenge.used_at = timezone.now()
    login_challenge.save(
        update_fields=["used_at"]
    )

    # Xodimni Django session'iga kiritamiz
    login(request, digital_key.user)

    return JsonResponse(
        {
            "success": True,
            "message": "✅ ERI imzosi tasdiqlandi.",
            "username": digital_key.user.username,
            "first_name": digital_key.user.first_name,
            "last_name": digital_key.user.last_name,
        }
    )


@login_required(login_url="user_login")
def user_dashboard(request):
    from messaging.models import Message, MessageRecipient, MessageState

    user = request.user

    inbox_count = MessageRecipient.objects.filter(
        recipient=user,
        message__status=Message.Status.SENT,
    ).count()

    sent_count = Message.objects.filter(
        sender=user,
        status=Message.Status.SENT,
    ).count()

    draft_count = Message.objects.filter(
        sender=user,
        status=Message.Status.DRAFT,
    ).count()

    saved_count = MessageState.objects.filter(
        user=user,
        is_starred=True,
        is_deleted=False,
    ).count()

    return render(
        request,
        "accounts/user_dashboard.html",
        {
            "user_obj": user,
            "inbox_count": inbox_count,
            "sent_count": sent_count,
            "draft_count": draft_count,
            "saved_count": saved_count,
        }
    )



@login_required(login_url="user_login")
def user_logout(request):
    logout(request)
    return redirect("user_login")
