import json
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from .models import MapMarker, RescueTeam


class AdminWorkflowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        user_model = get_user_model()
        self.admin = user_model.objects.create_user("admin_test", password="TestStrongPass!42", is_staff=True)
        self.other = user_model.objects.create_user("captain_test", password="TestStrongPass!42")

    def test_only_admin_can_log_in_and_read(self):
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 401)
        self.assertEqual(self.client.post("/api/login/", json.dumps({"username": "captain_test", "password": "TestStrongPass!42"}), content_type="application/json").status_code, 401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/markers/").status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post("/api/login/", json.dumps({"username": "admin_test", "password": "TestStrongPass!42"}), content_type="application/json").status_code, 200)

    def test_password_change_checks_current_password_and_keeps_session(self):
        self.client.force_login(self.admin)
        url = "/api/change-password/"
        wrong = self.client.post(
            url,
            json.dumps({
                "current_password": "wrong-password",
                "new_password": "NewSecurePass!84",
                "confirm_password": "NewSecurePass!84",
            }),
            content_type="application/json",
        )
        self.assertEqual(wrong.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password("TestStrongPass!42"))

        changed = self.client.post(
            url,
            json.dumps({
                "current_password": "TestStrongPass!42",
                "new_password": "NewSecurePass!84",
                "confirm_password": "NewSecurePass!84",
            }),
            content_type="application/json",
        )
        self.assertEqual(changed.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password("NewSecurePass!84"))
        self.assertEqual(self.client.get("/api/me/").status_code, 200)

    def test_marker_assignment_report_and_completion(self):
        self.client.force_login(self.admin)
        response = self.client.post("/api/markers/", json.dumps({"longitude": 85.379735, "latitude": 28.276811}), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        marker_id = response.json()["marker"]["id"]
        self.assertEqual(response.json()["marker"]["status"], "待分配")
        response = self.client.patch(f"/api/markers/{marker_id}/", json.dumps({"group": "抢险救援一组"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["marker"]["status"], "执行中")
        response = self.client.post(f"/api/markers/{marker_id}/reports/", {"content": "现场回报", "progress": "50", "completed": "false"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["marker"]["progress"], 50)
        self.assertEqual(self.client.post(f"/api/markers/{marker_id}/reports/", {"content": "倒退", "progress": "20", "completed": "false"}).status_code, 400)
        image = SimpleUploadedFile("site.png", b"\x89PNG\r\n\x1a\n" + b"x" * 24, content_type="image/png")
        response = self.client.post(f"/api/markers/{marker_id}/reports/", {"content": "任务完成", "progress": "100", "completed": "true", "photo": image})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["marker"]["status"], "已完成")
        self.assertEqual(MapMarker.objects.get(pk=marker_id).status, "已完成")
        photo_response = self.client.get(response.json()["marker"]["reports"][0]["photo_url"])
        self.assertEqual(photo_response.status_code, 200)
        photo_response.close()

    def test_reject_coordinate_outside_port_extent(self):
        self.client.force_login(self.admin)
        response = self.client.post("/api/markers/", json.dumps({"longitude": 0, "latitude": 0}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_admin_can_delete_marker(self):
        self.client.force_login(self.admin)
        response = self.client.post("/api/markers/", json.dumps({"longitude": 85.379735, "latitude": 28.276811}), content_type="application/json")
        marker_id = response.json()["marker"]["id"]
        response = self.client.delete(f"/api/markers/{marker_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_id"], marker_id)
        self.assertFalse(MapMarker.objects.filter(pk=marker_id).exists())

    def test_rescue_team_crud_updates_marker_assignment_catalog(self):
        self.client.force_login(self.admin)
        list_response = self.client.get("/api/rescue-teams/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["teams"]), 8)

        create_response = self.client.post(
            "/api/rescue-teams/",
            json.dumps({
                "category": "抢险救援组",
                "name": "抢险救援四组",
                "status": "上线",
                "captain": "",
                "captain_phone": "",
                "members": "",
                "member_contacts": "",
                "note": "",
            }),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        team_id = create_response.json()["team"]["id"]
        self.assertTrue(RescueTeam.objects.filter(name="抢险救援四组").exists())

        marker_response = self.client.post(
            "/api/markers/",
            json.dumps({"longitude": 85.379735, "latitude": 28.276811}),
            content_type="application/json",
        )
        marker_id = marker_response.json()["marker"]["id"]
        assignment = self.client.patch(
            f"/api/markers/{marker_id}/",
            json.dumps({"group": "抢险救援四组"}),
            content_type="application/json",
        )
        self.assertEqual(assignment.status_code, 200)
        self.assertEqual(assignment.json()["marker"]["group"], "抢险救援四组")

        rename = self.client.patch(
            f"/api/rescue-teams/{team_id}/",
            json.dumps({
                "category": "抢险救援组",
                "name": "抢险救援机动组",
                "status": "数据中",
                "captain": "",
                "captain_phone": "",
                "members": "",
                "member_contacts": "",
                "note": "",
            }),
            content_type="application/json",
        )
        self.assertEqual(rename.status_code, 200)
        self.assertEqual(rename.json()["team"]["status"], "上线")
        self.assertEqual(RescueTeam.objects.get(pk=team_id).status, "上线")
        self.assertEqual(MapMarker.objects.get(pk=marker_id).group, "抢险救援机动组")
        self.assertEqual(
            self.client.delete(f"/api/rescue-teams/{team_id}/").status_code,
            400,
        )

        MapMarker.objects.filter(pk=marker_id).delete()
        self.assertEqual(
            self.client.delete(f"/api/rescue-teams/{team_id}/").status_code,
            200,
        )

    def test_dashboard_reads_original_source_files(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["historical_sites"]["record_count"], 84)
        self.assertEqual(data["satellite"]["active"]["id"], "B040001100881610")
        self.assertEqual(data["map"]["port_wms"],
                         "/kqgis/rest/services/jilong_port_multitemporal/map/wms")
        self.assertEqual(data["map"]["port_default_scene_id"], "B040001100881610")
        self.assertEqual(len(data["map"]["port_scenes"]), 9)
        self.assertEqual({scene["layer"] for scene in data["map"]["port_scenes"]},
                         {str(value) for value in range(2, 11)})
        self.assertEqual([row["lake_count"] for row in data["ice_lakes"]["rows"]], ["101", "145"])
        self.assertEqual({topic["key"]: topic["record_count"] for topic in data["topics"]},
                         {"glacier": 170, "ice_lake": 145, "permafrost": 7, "historical": 84})
        topics = {topic["key"]: topic for topic in data["topics"]}
        self.assertEqual(topics["glacier"]["visual"]["items"][:2], ["桑青冰川", "普拥冰川"])
        self.assertEqual(topics["ice_lake"]["visual"]["items"],
                         [{"label": "1990", "value": "101"}, {"label": "2020", "value": "145"}])
        self.assertEqual(len(topics["permafrost"]["visual"]["items"]), 7)
        self.assertEqual(topics["permafrost"]["visual"]["items"][0]["value"], "0.182910722134000")
        self.assertEqual(topics["historical"]["visual"]["items"][0]["label"], "Q4XM-JLH-D00208")
        self.assertEqual(topics["historical"]["visual"]["items"][0]["value"], "2.76812999033e-01")
        self.assertEqual(data["map"]["county_wms"], "/kqgis/rest/services/jilong_county_atlas/map/wms")

    def test_team_leader_login_assignment_and_stage_reporting(self):
        team = RescueTeam.objects.get(name="抢险救援一组")
        team.captain = "测试组长"
        team.captain_phone = "13800000001"
        team.save(update_fields=["captain", "captain_phone", "updated_at"])

        leader_client = Client()
        self.assertEqual(
            leader_client.post(
                "/api/team-portal/login/",
                json.dumps({"phone": "13800000001", "password": "wrong"}),
                content_type="application/json",
            ).status_code,
            401,
        )
        login_response = leader_client.post(
            "/api/team-portal/login/",
            json.dumps({"phone": "138 0000 0001", "password": "123"}),
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["team"]["name"], team.name)
        self.assertEqual(
            leader_client.get("/api/team-portal/tasks/").json()["tasks"],
            [],
        )

        self.client.force_login(self.admin)
        marker_response = self.client.post(
            "/api/markers/",
            json.dumps({"longitude": 85.379735, "latitude": 28.276811}),
            content_type="application/json",
        )
        marker_id = marker_response.json()["marker"]["id"]
        assignment = self.client.patch(
            f"/api/markers/{marker_id}/",
            json.dumps({"group": team.name}),
            content_type="application/json",
        )
        self.assertEqual(assignment.status_code, 200)
        task_number = assignment.json()["marker"]["task_number"]
        self.assertRegex(task_number, rf"^JL-\d{{8}}-{marker_id:06d}$")
        self.assertEqual(assignment.json()["marker"]["current_stage"], 1)
        self.assertEqual(
            assignment.json()["marker"]["stage_label"],
            "已分配任务，请尽快到达",
        )

        tasks_response = leader_client.get("/api/team-portal/tasks/")
        self.assertEqual(tasks_response.status_code, 200)
        self.assertEqual(tasks_response.json()["tasks"][0]["task_number"], task_number)

        image = SimpleUploadedFile(
            "leader-site.png",
            b"\x89PNG\r\n\x1a\n" + b"x" * 24,
            content_type="image/png",
        )
        report = leader_client.post(
            f"/api/team-portal/tasks/{marker_id}/report/",
            {"advance": "true", "photo": image},
        )
        self.assertEqual(report.status_code, 201)
        self.assertEqual(report.json()["marker"]["current_stage"], 2)
        self.assertEqual(report.json()["marker"]["stage_label"], "任务中")
        self.assertEqual(report.json()["marker"]["progress"], 50)
        photo_url = report.json()["marker"]["reports"][0]["photo_url"]
        photo_response = leader_client.get(photo_url)
        self.assertEqual(photo_response.status_code, 200)
        photo_response.close()

        report = leader_client.post(
            f"/api/team-portal/tasks/{marker_id}/report/",
            {"advance": "true"},
        )
        self.assertEqual(report.status_code, 201)
        self.assertEqual(report.json()["marker"]["current_stage"], 3)
        self.assertEqual(report.json()["marker"]["stage_label"], "任务完成")
        self.assertEqual(report.json()["marker"]["status"], "已完成")
        self.assertEqual(report.json()["marker"]["progress"], 100)
        marker = MapMarker.objects.get(pk=marker_id)
        self.assertEqual(marker.task_number, task_number)
        self.assertEqual(marker.status, "已完成")
