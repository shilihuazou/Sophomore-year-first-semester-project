from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=80, unique=True)
    captain = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rescue_team")
    status = models.CharField(max_length=20, default="未上报")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Mission(models.Model):
    STATUS = [(x, x) for x in ("待派遣", "执行中", "已完成")]
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="missions")
    status = models.CharField(max_length=12, choices=STATUS, default="待派遣")
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_missions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class MissionReport(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="reports")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class RescueTeam(models.Model):
    CATEGORIES = [
        ("抢险救援组", "抢险救援组"),
        ("医疗治疗组", "医疗治疗组"),
        ("电力保障组", "电力保障组"),
        ("地质监测组", "地质监测组"),
        ("群众安置组", "群众安置组"),
    ]
    STATUSES = [
        ("上线", "上线"),
        ("数据中", "数据中"),
        ("未上线", "未上线"),
        ("异常", "异常"),
    ]

    category = models.CharField(max_length=20, choices=CATEGORIES)
    name = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="上线")
    captain = models.CharField(max_length=80, blank=True)
    captain_phone = models.CharField(max_length=80, blank=True)
    leader_password = models.CharField(max_length=128, blank=True)
    members = models.TextField(blank=True)
    member_contacts = models.TextField(blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["captain_phone"],
                condition=~models.Q(captain_phone=""),
                name="unique_nonblank_captain_phone",
            ),
        ]

    def __str__(self):
        return self.name


class MapMarker(models.Model):
    STATUS = [(name, name) for name in ("待分配", "执行中", "已完成")]
    longitude = models.FloatField()
    latitude = models.FloatField()
    group = models.CharField(max_length=80, blank=True)
    task_number = models.CharField(max_length=40, unique=True, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="待分配")
    progress = models.PositiveSmallIntegerField(default=0)
    current_stage = models.PositiveSmallIntegerField(default=0)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="map_markers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class MarkerReport(models.Model):
    marker = models.ForeignKey(MapMarker, on_delete=models.CASCADE, related_name="reports")
    content = models.TextField(blank=True)
    progress = models.PositiveSmallIntegerField()
    completed = models.BooleanField(default=False)
    photo = models.FileField(upload_to="marker_reports/%Y/%m/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
