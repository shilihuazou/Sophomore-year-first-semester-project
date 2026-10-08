from django.db import migrations, models


def rename_existing_groups(apps, schema_editor):
    marker = apps.get_model("core", "MapMarker")
    marker.objects.filter(group="抢险救援组").update(group="抢险救援一组")
    marker.objects.filter(group="医疗治疗组").update(group="医疗治疗一组")


class Migration(migrations.Migration):
    dependencies = [("core", "0002_mapmarker_markerreport")]

    operations = [
        migrations.RunPython(rename_existing_groups, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="mapmarker",
            name="group",
            field=models.CharField(
                blank=True,
                choices=[
                    ("抢险救援一组", "抢险救援一组"),
                    ("抢险救援二组", "抢险救援二组"),
                    ("抢险救援三组", "抢险救援三组"),
                    ("医疗治疗一组", "医疗治疗一组"),
                    ("医疗治疗二组", "医疗治疗二组"),
                    ("电力保障组", "电力保障组"),
                    ("地质监测组", "地质监测组"),
                    ("群众安置组", "群众安置组"),
                ],
                max_length=20,
            ),
        ),
    ]
