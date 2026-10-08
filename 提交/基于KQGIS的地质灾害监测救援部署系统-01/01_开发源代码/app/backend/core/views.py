import math
import re
import struct
from pathlib import Path

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .api_utils import admin_required, error_response, json_payload, team_leader_required
from .models import MapMarker, MarkerReport, RescueTeam
from .serializers import marker_json, rescue_team_json, user_json
from .services.dashboard import build_dashboard


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    return JsonResponse({"ready": True})


@require_http_methods(["POST"])
def sign_in(request):
    data = json_payload(request)
    user = authenticate(
        request,
        username=str(data.get("username", "")),
        password=str(data.get("password", "")),
    )
    if not user or not user.is_active or not user.is_staff:
        return error_response("账号或密码错误", 401)
    login(request, user)
    return JsonResponse({"user": user_json(user)})


@admin_required
@require_http_methods(["POST"])
def sign_out(request):
    logout(request)
    return JsonResponse({"ok": True})


@admin_required
@require_http_methods(["GET"])
def me(request):
    return JsonResponse({"user": user_json(request.user)})


@admin_required
@require_http_methods(["POST"])
def change_password(request):
    data = json_payload(request)
    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    if not request.user.check_password(current_password):
        return error_response("原密码不正确")
    if new_password != confirm_password:
        return error_response("两次输入的新密码不一致")
    if current_password == new_password:
        return error_response("新密码不能与原密码相同")

    try:
        validate_password(new_password, user=request.user)
    except ValidationError as exc:
        return error_response("；".join(exc.messages))

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return JsonResponse({"ok": True})


@admin_required
@require_http_methods(["GET"])
def dashboard(request):
    try:
        return JsonResponse(build_dashboard())
    except (OSError, ValueError, StopIteration, KeyError, struct.error) as exc:
        return error_response(f"原始数据暂不可读取：{exc}", 503)


def normalize_phone(value):
    return re.sub(r"\D", "", str(value or ""))


def rescue_team_payload(data, status="上线", current_team_id=None):
    captain_phone = normalize_phone(data.get("captain_phone", ""))
    values = {
        "category": str(data.get("category", "")).strip(),
        "name": str(data.get("name", "")).strip(),
        "status": status,
        "captain": str(data.get("captain", "")).strip(),
        "captain_phone": captain_phone,
        "members": str(data.get("members", "")).strip(),
        "member_contacts": str(data.get("member_contacts", "")).strip(),
        "note": str(data.get("note", "")).strip(),
    }
    if values["category"] not in dict(RescueTeam.CATEGORIES):
        return None, "请选择有效的救援类别"
    if not values["name"] or len(values["name"]) > 80:
        return None, "请填写不超过 80 字的组名"
    if len(values["captain"]) > 80 or len(values["captain_phone"]) > 80:
        return None, "组长及联系方式均不能超过 80 字"
    if captain_phone and not 6 <= len(captain_phone) <= 20:
        return None, "组长手机号须为 6–20 位数字"
    phone_query = RescueTeam.objects.filter(captain_phone=captain_phone)
    if current_team_id:
        phone_query = phone_query.exclude(pk=current_team_id)
    if captain_phone and phone_query.exists():
        return None, "该组长手机号已用于其他救援组"
    if any(len(values[field]) > 2000 for field in ("members", "member_contacts", "note")):
        return None, "成员、成员联系方式和备注均不能超过 2000 字"
    return values, None


@admin_required
@require_http_methods(["GET", "POST"])
def rescue_teams(request):
    if request.method == "GET":
        queryset = RescueTeam.objects.all()
        return JsonResponse({
            "categories": [value for value, _ in RescueTeam.CATEGORIES],
            "teams": [rescue_team_json(team) for team in queryset],
        })

    values, error = rescue_team_payload(json_payload(request))
    if error:
        return error_response(error)
    try:
        team = RescueTeam.objects.create(
            **values,
            leader_password=make_password("123"),
        )
    except IntegrityError:
        return error_response("组名已存在")
    return JsonResponse({"team": rescue_team_json(team)}, status=201)


@admin_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def rescue_team_detail(request, team_id):
    team = RescueTeam.objects.filter(pk=team_id).first()
    if not team:
        return error_response("救援组不存在", 404)

    if request.method == "DELETE":
        if MapMarker.objects.filter(group=team.name).exists():
            return error_response("该救援组已有标记任务，不能删除")
        deleted_id = team.id
        team.delete()
        return JsonResponse({"ok": True, "deleted_id": deleted_id})

    if request.method == "PATCH":
        values, error = rescue_team_payload(
            json_payload(request),
            status=team.status,
            current_team_id=team.id,
        )
        if error:
            return error_response(error)
        previous_name = team.name
        try:
            with transaction.atomic():
                for field, value in values.items():
                    setattr(team, field, value)
                team.save()
                if previous_name != team.name:
                    MapMarker.objects.filter(group=previous_name).update(group=team.name)
        except IntegrityError:
            return error_response("组名已存在")

    return JsonResponse({"team": rescue_team_json(team)})


@admin_required
@require_http_methods(["GET", "POST"])
def markers(request):
    if request.method == "GET":
        queryset = MapMarker.objects.prefetch_related("reports")
        return JsonResponse({
            "markers": [marker_json(item, with_reports=True) for item in queryset]
        })

    data = json_payload(request)
    try:
        longitude = float(data.get("longitude"))
        latitude = float(data.get("latitude"))
    except (TypeError, ValueError):
        return error_response("坐标格式不正确")
    if not (math.isfinite(longitude) and math.isfinite(latitude)):
        return error_response("坐标格式不正确")

    port_scenes = build_dashboard()["map"]["port_scenes"]
    inside_published_scene = any(
        scene["bbox"][0] <= longitude <= scene["bbox"][2]
        and scene["bbox"][1] <= latitude <= scene["bbox"][3]
        for scene in port_scenes
    )
    if not inside_published_scene:
        return error_response("标记只能放在已发布的吉隆口岸及周边影像范围内")

    marker = MapMarker.objects.create(
        longitude=longitude,
        latitude=latitude,
        created_by=request.user,
    )
    return JsonResponse({"marker": marker_json(marker, with_reports=True)}, status=201)


@admin_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def marker_detail(request, marker_id):
    marker = MapMarker.objects.prefetch_related("reports").filter(pk=marker_id).first()
    if not marker:
        return error_response("标记点不存在", 404)

    if request.method == "DELETE":
        photo_names = [report.photo.name for report in marker.reports.all() if report.photo]
        storage = MarkerReport._meta.get_field("photo").storage

        def delete_photos():
            for name in photo_names:
                storage.delete(name)

        with transaction.atomic():
            marker.delete()
            transaction.on_commit(delete_photos)
        return JsonResponse({"ok": True, "deleted_id": marker_id})

    if request.method == "PATCH":
        group = str(json_payload(request).get("group", ""))
        if not RescueTeam.objects.filter(name=group).exists():
            return error_response("请选择有效救援组别")
        if marker.status != "待分配":
            return error_response("标记点已分配，不可重复分配")
        marker.group = group
        marker.task_number = (
            f"JL-{marker.created_at.strftime('%Y%m%d')}-{marker.id:06d}"
        )
        marker.status = "执行中"
        marker.current_stage = 1
        marker.progress = 0
        marker.save(update_fields=[
            "group",
            "task_number",
            "status",
            "current_stage",
            "progress",
            "updated_at",
        ])

    return JsonResponse({"marker": marker_json(marker, with_reports=True)})


def valid_image(upload):
    if not upload or upload.size > 10 * 1024 * 1024 or upload.size == 0:
        return False
    header = upload.read(16)
    upload.seek(0)
    suffix = Path(upload.name).suffix.lower()
    return (
        (header.startswith(b"\xff\xd8\xff") and suffix in (".jpg", ".jpeg"))
        or (header.startswith(b"\x89PNG\r\n\x1a\n") and suffix == ".png")
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP" and suffix == ".webp")
    )


@admin_required
@require_http_methods(["POST"])
def marker_reports(request, marker_id):
    marker = MapMarker.objects.filter(pk=marker_id).first()
    if not marker:
        return error_response("标记点不存在", 404)
    if marker.status != "执行中":
        return error_response("只有执行中的标记点可上报")

    try:
        progress = int(request.POST.get("progress", ""))
    except (TypeError, ValueError):
        return error_response("请填写 0–100 的任务进度")
    completed = request.POST.get("completed") == "true"
    if not 0 <= progress <= 100 or progress < marker.progress:
        return error_response("进度须为 0–100 且不能倒退")
    if completed and progress != 100:
        return error_response("上报完成时进度必须为 100")

    content = request.POST.get("content", "").strip()
    photo = request.FILES.get("photo")
    if len(content) > 2000 or (not content and not photo and not completed):
        return error_response("请填写不超过 2000 字的上报内容，或上传现场图片")
    if photo and not valid_image(photo):
        return error_response("图片仅支持 10 MB 内的 JPEG、PNG 或 WebP")

    with transaction.atomic():
        MarkerReport.objects.create(
            marker=marker,
            content=content,
            progress=progress,
            completed=completed,
            photo=photo or "",
        )
        marker.progress = progress
        marker.current_stage = 3 if completed else (2 if progress else 1)
        if completed:
            marker.status = "已完成"
        marker.save(update_fields=[
            "progress",
            "current_stage",
            "status",
            "updated_at",
        ])

    marker.refresh_from_db()
    return JsonResponse({"marker": marker_json(marker, with_reports=True)}, status=201)


@require_http_methods(["GET"])
def marker_photo(request, report_id):
    report = MarkerReport.objects.select_related("marker").filter(pk=report_id).first()
    if not report or not report.photo:
        return error_response("图片不存在", 404)
    leader_team_id = request.session.get("leader_team_id")
    leader_team = RescueTeam.objects.filter(pk=leader_team_id).first()
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_assigned_leader = leader_team and report.marker.group == leader_team.name
    if not is_admin and not is_assigned_leader:
        return error_response("无权查看该图片", 403 if request.user.is_authenticated or leader_team_id else 401)
    suffix = Path(report.photo.name).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")
    response = FileResponse(report.photo.open("rb"), content_type=content_type)
    response["Content-Disposition"] = "inline"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def leader_team_json(team):
    return {
        "id": team.id,
        "category": team.category,
        "name": team.name,
        "captain": team.captain,
        "captain_phone": team.captain_phone,
    }


@require_http_methods(["POST"])
def team_leader_login(request):
    data = json_payload(request)
    phone = normalize_phone(data.get("phone", ""))
    password = str(data.get("password", ""))
    team = RescueTeam.objects.filter(captain_phone=phone).first()
    password_matches = bool(
        team
        and (
            check_password(password, team.leader_password)
            if team.leader_password
            else password == "123"
        )
    )
    if not team or not phone or not password_matches:
        return error_response("手机号或密码错误", 401)
    if not team.leader_password:
        team.leader_password = make_password("123")
        team.save(update_fields=["leader_password", "updated_at"])
    request.session["leader_team_id"] = team.id
    return JsonResponse({"team": leader_team_json(team)})


@team_leader_required
@require_http_methods(["POST"])
def team_leader_logout(request):
    request.session.pop("leader_team_id", None)
    return JsonResponse({"ok": True})


@team_leader_required
@require_http_methods(["GET"])
def team_leader_me(request):
    return JsonResponse({"team": leader_team_json(request.rescue_team)})


@team_leader_required
@require_http_methods(["GET"])
def team_leader_tasks(request):
    queryset = MapMarker.objects.prefetch_related("reports").filter(
        group=request.rescue_team.name,
    )[:20]
    return JsonResponse({
        "team": leader_team_json(request.rescue_team),
        "tasks": [marker_json(marker, with_reports=True) for marker in queryset],
    })


@team_leader_required
@require_http_methods(["POST"])
def team_leader_task_report(request, marker_id):
    marker = MapMarker.objects.filter(
        pk=marker_id,
        group=request.rescue_team.name,
    ).first()
    if not marker:
        return error_response("任务不存在或未分配给当前救援组", 404)
    if marker.status != "执行中":
        return error_response("该任务当前不可上报")

    advance = request.POST.get("advance") == "true"
    photo = request.FILES.get("photo")
    if not advance and not photo:
        return error_response("请选择进入下一阶段或上传现场图片")
    if photo and not valid_image(photo):
        return error_response("图片仅支持 10 MB 内的 JPEG、PNG 或 WebP")

    current_stage = max(marker.current_stage, 1)
    next_stage = min(current_stage + 1, 3) if advance else current_stage
    next_progress = {1: 0, 2: 50, 3: 100}[next_stage]
    completed = next_stage == 3
    content = (
        ("组长上报任务完成" if completed else "组长上报进入任务中阶段")
        if advance
        else "组长上传现场图片"
    )
    with transaction.atomic():
        MarkerReport.objects.create(
            marker=marker,
            content=content,
            progress=next_progress,
            completed=completed,
            photo=photo or "",
        )
        marker.current_stage = next_stage
        marker.progress = next_progress
        if completed:
            marker.status = "已完成"
        marker.save(update_fields=[
            "current_stage",
            "progress",
            "status",
            "updated_at",
        ])

    marker.refresh_from_db()
    return JsonResponse({
        "marker": marker_json(
            MapMarker.objects.prefetch_related("reports").get(pk=marker.id),
            with_reports=True,
        )
    }, status=201)
