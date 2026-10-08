import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "创建唯一的应用演示管理员；已有账号不重置密码"

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = "admin"
        user = user_model.objects.filter(username=username).first()
        if user:
            self.stdout.write(f"{username}: 已存在，密码保持不变")
        else:
            password = secrets.token_urlsafe(12)
            user_model.objects.create_user(username=username, password=password, is_staff=True)
            self.stdout.write(f"{username}: {password}")
        self.stdout.write("仅管理员可登录应用；未生成任何标记点、救援进度或现场图片。")
