# 登录平台（Django + Vue3）— 洪水监测主题

基于 **Django 后端 + Vue 3 前端** 的登录平台，**洪水监测**主题：登录页/注册页背景为**洪水主题照片幻灯片式循环轮播**（淡入淡出 + 缓慢放大动效，**每 6 秒自动切换，无箭头、无指示点**），支持**账号注册**与登录。

> 本机环境已配置好：**Python 3.8.10**（`C:\Users\魏海晨\AppData\Local\Programs\Python\Python38`）+ **Django 4.2.30**（4.2 是支持 Python 3.8 的最后一个版本），虚拟环境位于项目内 `.venv`，依赖已安装，数据库已迁移，测试账号已创建。

## 项目结构

```
login-platform/
├── .venv/                   # Python 3.8 虚拟环境（已建好，Django 4.2.30 已装）
├── backend/                 # Django 后端（Python）
│   ├── manage.py
│   ├── backend/             # 项目配置（settings.py / urls.py）
│   ├── requirements.txt     # Django>=4.2,<4.3
│   └── users/               # 登录应用
│       ├── views.py         # 注册 / 登录 / 退出 / 当前用户 四个接口
│       └── urls.py          # /api/register/  /api/login/  /api/logout/  /api/user/
└── frontend/                # Vue 3 前端（Vite）
    ├── vite.config.js       # 开发代理：/api -> http://127.0.0.1:8000
    └── src/
        ├── views/Login.vue     # 登录页（洪水照片自动轮播背景）
        ├── views/Register.vue  # 注册页（同样式轮播背景）
        ├── views/Welcome.vue   # 登录成功后的欢迎页
        ├── assets/bg-config.js # ★ 轮播照片配置，换照片改这里
        └── assets/bg/          # 轮播照片目录（内置 4 张洪水监测主题图）
```

## 一、用 PyCharm 打开项目

1. PyCharm → **File → Open**，选择 `login-platform` 文件夹打开。
2. **解释器**：PyCharm 会自动识别项目里的 `.venv`（Python 3.8.10）。如果没有自动识别：
   **Settings → Project: login-platform → Python Interpreter → Add Interpreter → Existing → 选择 `login-platform\.venv\Scripts\python.exe`**。
3. 后端依赖已装好，无需再装；如需重装：
   ```bash
   pip install -r backend/requirements.txt
   ```

## 二、启动后端（Django）

PyCharm 底部 **Terminal** 中执行：

```bash
cd backend
..\.venv\Scripts\python manage.py runserver
```

后端地址：http://127.0.0.1:8000

> 数据库已迁移好，测试账号已创建。若删除了 `db.sqlite3`，重新执行：
> ```bash
> ..\.venv\Scripts\python manage.py migrate
> ..\.venv\Scripts\python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('admin','admin@test.com','123456')"
> ```

## 三、启动前端（Vue）

另开一个 Terminal（或独立命令行）：

```bash
cd frontend
npm install        # 首次运行需要，node_modules 已装好则跳过
npm run dev
```

前端地址：**http://127.0.0.1:5173**（浏览器打开这个地址）
开发环境下 `/api` 请求已由 Vite 自动代理到 Django，无跨域问题。

## 四、注册与登录测试

- **注册**：登录页点"立即注册"→ 填写用户名（≥3 字符）、密码（≥6 位）、确认密码 → 注册成功自动跳回登录页并提示。
- **测试账号**：`admin / 123456`（已内置）
- 登录成功后会跳转到欢迎页；退出登录会回到登录页。
- 访问 `/welcome` 未登录时会自动跳回登录页（路由守卫）。

## 五、接口说明

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/register/` | POST | 入参 `{"username":"...","password":"...","confirm_password":"..."}`，成功返回 `code:0` |
| `/api/login/` | POST | 入参 `{"username":"admin","password":"123456"}`，成功返回 `code:0` 并写入会话 |
| `/api/logout/` | GET | 退出登录 |
| `/api/user/` | GET | 返回当前登录用户，未登录返回 `code:2` |

## 六、更换轮播背景照片

打开 `frontend/src/assets/bg-config.js`：

```js
import flood1 from './bg/flood1-farmland.jpg'
// 1. 把你的照片放进 src/assets/bg/ 目录
// 2. import 进来，加入数组即可，数组顺序 = 播放顺序
export const backgroundPhotos = [
  { src: flood1, title: '洪水淹没田野' },
  ...
]
```

想调整切换速度，改 `Login.vue` 和 `Register.vue` 里的 `INTERVAL = 6000`（单位毫秒）。

## 七、改用 MySQL（可选）

默认使用 SQLite（零配置，开箱即用）。如需 MySQL 8.0，编辑
`backend/backend/settings.py`，取消注释其中已写好的 MySQL 配置段，并执行：

```bash
..\.venv\Scripts\python -m pip install pymysql
..\.venv\Scripts\python manage.py migrate
```

## 常见问题

- **登录提示"网络错误"**：确认 Django 已在 8000 端口运行。
- **端口被占用**：`runserver` 加端口参数如 `python manage.py runserver 8001`，并同步修改 `frontend/vite.config.js` 里的代理 target。
- **Python 版本提醒**：本机 PyCharm 用的是 Python 3.8，务必使用项目内 `.venv` 解释器；Django 4.2 是支持 3.8 的最后一个版本，不要升级到 Django 5/6（需要 Python 3.10/3.12+）。
