from django.db import migrations, models


DEFAULT_TEAMS = [
    ("抢险救援组", "抢险救援一组"),
    ("抢险救援组", "抢险救援二组"),
    ("抢险救援组", "抢险救援三组"),
    ("医疗治疗组", "医疗治疗一组"),
    ("医疗治疗组", "医疗治疗二组"),
    ("电力保障组", "电力保障组"),
    ("地质监测组", "地质监测组"),
    ("群众安置组", "群众安置组"),
]


def seed_rescue_teams(apps, schema_editor):
    rescue_team = apps.get_model("core", "RescueTeam")
    for category, name in DEFAULT_TEAMS:
        rescue_team.objects.get_or_create(
            name=name,
            defaults={"category": category, "status": "上线"},
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0003_fixed_rescue_teams")]

    operations = [
        migrations.CreateModel(
            name="RescueTeam",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("抢险救援组", "抢险救援组"),
                            ("医疗治疗组", "医疗治疗组"),
                            ("电力保障组", "电力保障组"),
                            ("地质监测组", "地质监测组"),
                            ("群众安置组", "群众安置组"),
                        ],
                        max_length=20,
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("上线", "上线"),
                            ("数据中", "数据中"),
                            ("未上线", "未上线"),
                            ("异常", "异常"),
                        ],
                        default="上线",
                        max_length=12,
                    ),
                ),
                ("captain", models.CharField(blank=True, max_length=80)),
                ("captain_phone", models.CharField(blank=True, max_length=80)),
                ("members", models.TextField(blank=True)),
                ("member_contacts", models.TextField(blank=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["category", "created_at", "id"]},
        ),
        migrations.RunPython(seed_rescue_teams, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="mapmarker",
            name="group",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
