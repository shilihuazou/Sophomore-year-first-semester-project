"""登录平台 API 视图：注册 / 登录 / 退出 / 当前用户"""
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def register_view(request):
    """POST /api/register/  body: {"username": "...", "password": "...", "confirm_password": "..."}"""
    if request.method != 'POST':
        return JsonResponse({'code': 1, 'msg': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'code': 1, 'msg': '请求体格式错误'})

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not username or not password:
        return JsonResponse({'code': 1, 'msg': '用户名和密码不能为空'})
    if len(username) < 3:
        return JsonResponse({'code': 1, 'msg': '用户名至少 3 个字符'})
    if len(password) < 6:
        return JsonResponse({'code': 1, 'msg': '密码至少 6 位'})
    if password != confirm_password:
        return JsonResponse({'code': 1, 'msg': '两次输入的密码不一致'})
    if User.objects.filter(username=username).exists():
        return JsonResponse({'code': 1, 'msg': '该用户名已被注册'})

    User.objects.create_user(username=username, password=password)
    return JsonResponse({'code': 0, 'msg': '注册成功，请登录'})


@csrf_exempt
def login_view(request):
    """POST /api/login/  body: {"username": "...", "password": "..."}"""
    if request.method != 'POST':
        return JsonResponse({'code': 1, 'msg': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'code': 1, 'msg': '请求体格式错误'})

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return JsonResponse({'code': 1, 'msg': '用户名和密码不能为空'})

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'code': 1, 'msg': '用户名或密码错误'})

    if not user.is_active:
        return JsonResponse({'code': 1, 'msg': '该账号已被禁用'})

    login(request, user)  # 写入 session，后续请求携带 Cookie 即视为已登录
    return JsonResponse({
        'code': 0,
        'msg': '登录成功',
        'data': {
            'username': user.username,
            'is_staff': user.is_staff,
        },
    })


@login_required
def logout_view(request):
    """GET/POST /api/logout/  退出登录"""
    logout(request)
    return JsonResponse({'code': 0, 'msg': '已退出登录'})


def current_user(request):
    """GET /api/user/  返回当前登录用户；未登录返回 code=2"""
    if not request.user.is_authenticated:
        return JsonResponse({'code': 2, 'msg': '未登录'})
    return JsonResponse({
        'code': 0,
        'msg': 'ok',
        'data': {
            'username': request.user.username,
            'is_staff': request.user.is_staff,
        },
    })
