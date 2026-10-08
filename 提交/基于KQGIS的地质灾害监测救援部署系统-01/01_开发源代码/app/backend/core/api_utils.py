import json
from functools import wraps

from django.http import JsonResponse


def error_response(message, status=400):
    """Return the API's consistent JSON error shape."""
    return JsonResponse({"error": message}, status=status)


def json_payload(request):
    """Read a JSON object body; malformed or non-object bodies become empty."""
    try:
        value = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def admin_required(view):
    """Require the single administrator role used by this application."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error_response("请先登录", 401)
        if not request.user.is_staff:
            return error_response("仅管理员可使用此平台", 403)
        return view(request, *args, **kwargs)

    return wrapped


def team_leader_required(view):
    """Require a rescue-team leader session without changing admin auth."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        from .models import RescueTeam

        team_id = request.session.get("leader_team_id")
        team = RescueTeam.objects.filter(pk=team_id).first()
        if not team:
            request.session.pop("leader_team_id", None)
            return error_response("请先登录组长端", 401)
        request.rescue_team = team
        return view(request, *args, **kwargs)

    return wrapped
