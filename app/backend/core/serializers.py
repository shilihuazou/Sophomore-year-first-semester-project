def user_json(user):
    return {
        "id": user.id,
        "username": user.username,
        "role": "admin",
        "team": None,
    }


def team_json(team):
    return {
        "id": team.id,
        "name": team.name,
        "status": team.status,
        "note": team.note,
        "captain": team.captain.username,
        "created_at": team.created_at.isoformat(),
    }


def rescue_team_json(team):
    return {
        "id": team.id,
        "category": team.category,
        "name": team.name,
        "status": team.status,
        "captain": team.captain,
        "captain_phone": team.captain_phone,
        "members": team.members,
        "member_contacts": team.member_contacts,
        "note": team.note,
        "created_at": team.created_at.isoformat(),
        "updated_at": team.updated_at.isoformat(),
    }


def mission_json(mission, with_reports=False):
    result = {
        "id": mission.id,
        "title": mission.title,
        "description": mission.description,
        "team_id": mission.team_id,
        "team_name": mission.team.name,
        "status": mission.status,
        "longitude": mission.longitude,
        "latitude": mission.latitude,
        "created_at": mission.created_at.isoformat(),
    }
    if with_reports:
        result["reports"] = [
            {
                "id": report.id,
                "content": report.content,
                "author": report.author.username,
                "created_at": report.created_at.isoformat(),
            }
            for report in mission.reports.select_related("author")
        ]
    return result


def marker_json(marker, with_reports=False):
    result = {
        "id": marker.id,
        "task_number": marker.task_number,
        "longitude": marker.longitude,
        "latitude": marker.latitude,
        "group": marker.group,
        "status": marker.status,
        "progress": marker.progress,
        "current_stage": marker.current_stage,
        "stage_label": marker_stage_label(marker),
        "note": marker.note,
        "created_at": marker.created_at.isoformat(),
        "updated_at": marker.updated_at.isoformat(),
    }
    if with_reports:
        result["reports"] = [
            {
                "id": report.id,
                "content": report.content,
                "progress": report.progress,
                "completed": report.completed,
                "photo_url": f"/api/marker-reports/{report.id}/photo/" if report.photo else None,
                "created_at": report.created_at.isoformat(),
            }
            for report in marker.reports.all()
        ]
    return result


def marker_stage_label(marker):
    if marker.status == "待分配":
        return "未分配"
    if marker.status == "已完成":
        return "任务完成"
    if marker.current_stage <= 1:
        return "已分配任务，请尽快到达"
    return "任务中"
