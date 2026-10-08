"""Compatibility API for the earlier team/mission prototype.

The current product uses map markers for dispatch. These endpoints remain available
for existing local data and integrations, but they are not used by the Vue client.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .api_utils import admin_required, error_response, json_payload
from .models import Mission, MissionReport, Team
from .serializers import mission_json, team_json


@admin_required
@require_http_methods(["GET"])
def teams(request):
    queryset = Team.objects.select_related("captain").order_by("id")
    return JsonResponse({"teams": [team_json(item) for item in queryset]})


@admin_required
@require_http_methods(["GET", "PATCH"])
def team_detail(request, team_id):
    team = Team.objects.select_related("captain").filter(pk=team_id).first()
    if not team:
        return error_response("队伍不存在", 404)
    if request.method == "PATCH":
        data = json_payload(request)
        status = data.get("status")
        if status not in ("未上报", "待命", "救援中", "异常", "已结束"):
            return error_response("无效的队伍状态")
        team.status = status
        team.note = str(data.get("note", team.note))[:2000]
        team.save(update_fields=["status", "note"])
    return JsonResponse({"team": team_json(team)})


@admin_required
@require_http_methods(["GET", "POST"])
def missions(request):
    if request.method == "GET":
        queryset = Mission.objects.select_related("team")
        return JsonResponse({"missions": [mission_json(item) for item in queryset]})

    data = json_payload(request)
    title = str(data.get("title", "")).strip()
    if not title or len(title) > 120:
        return error_response("请填写不超过 120 字的任务名称")
    team = Team.objects.filter(pk=data.get("team_id")).first()
    if not team:
        return error_response("请选择已有演示队伍")

    longitude, latitude = data.get("longitude"), data.get("latitude")
    if (longitude is None) != (latitude is None):
        return error_response("经纬度必须同时填写或同时留空")
    if longitude is not None:
        try:
            longitude, latitude = float(longitude), float(latitude)
        except (TypeError, ValueError):
            return error_response("经纬度格式不正确")
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            return error_response("经纬度超出范围")

    mission = Mission.objects.create(
        title=title,
        description=str(data.get("description", ""))[:2000],
        team=team,
        longitude=longitude,
        latitude=latitude,
        created_by=request.user,
    )
    return JsonResponse({"mission": mission_json(mission)}, status=201)


def visible_mission(mission_id):
    return Mission.objects.select_related("team").filter(pk=mission_id).first()


@admin_required
@require_http_methods(["GET", "PATCH"])
def mission_detail(request, mission_id):
    mission = visible_mission(mission_id)
    if not mission:
        return error_response("任务不存在或无权查看", 404)
    if request.method == "PATCH":
        status = json_payload(request).get("status")
        if status not in dict(Mission.STATUS):
            return error_response("无效的任务状态")
        mission.status = status
        mission.save(update_fields=["status"])
    return JsonResponse({"mission": mission_json(mission, with_reports=True)})


@admin_required
@require_http_methods(["POST"])
def mission_reports(request, mission_id):
    mission = visible_mission(mission_id)
    if not mission:
        return error_response("任务不存在或无权汇报", 404)
    content = str(json_payload(request).get("content", "")).strip()
    if not content or len(content) > 2000:
        return error_response("请填写不超过 2000 字的现场情况")
    report = MissionReport.objects.create(mission=mission, author=request.user, content=content)
    return JsonResponse({
        "report": {
            "id": report.id,
            "content": report.content,
            "author": report.author.username,
            "created_at": report.created_at.isoformat(),
        }
    }, status=201)
