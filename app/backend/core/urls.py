from django.urls import path
from . import legacy_views, views

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("login/", views.sign_in, name="login"),
    path("logout/", views.sign_out, name="logout"),
    path("me/", views.me, name="me"),
    path("change-password/", views.change_password, name="change-password"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("rescue-teams/", views.rescue_teams, name="rescue-teams"),
    path("rescue-teams/<int:team_id>/", views.rescue_team_detail, name="rescue-team-detail"),
    path("teams/", legacy_views.teams, name="teams"),
    path("teams/<int:team_id>/", legacy_views.team_detail, name="team-detail"),
    path("missions/", legacy_views.missions, name="missions"),
    path("missions/<int:mission_id>/", legacy_views.mission_detail, name="mission-detail"),
    path("missions/<int:mission_id>/reports/", legacy_views.mission_reports, name="mission-reports"),
    path("markers/", views.markers, name="markers"),
    path("markers/<int:marker_id>/", views.marker_detail, name="marker-detail"),
    path("markers/<int:marker_id>/reports/", views.marker_reports, name="marker-reports"),
    path("marker-reports/<int:report_id>/photo/", views.marker_photo, name="marker-photo"),
    path("team-portal/login/", views.team_leader_login, name="team-leader-login"),
    path("team-portal/logout/", views.team_leader_logout, name="team-leader-logout"),
    path("team-portal/me/", views.team_leader_me, name="team-leader-me"),
    path("team-portal/tasks/", views.team_leader_tasks, name="team-leader-tasks"),
    path(
        "team-portal/tasks/<int:marker_id>/report/",
        views.team_leader_task_report,
        name="team-leader-task-report",
    ),
]
