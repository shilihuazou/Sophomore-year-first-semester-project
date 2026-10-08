# 项目文件夹说明

更新时间：2026-09-26

```text
CangQiongPj/
├─ app/                       正式应用
│  ├─ backend/               Django API、SQLite 与图片存储
│  ├─ frontend/              管理员登录、智慧大屏、调度后台
│  ├─ team-frontend/         救援组长任务端
│  └─ start-services.ps1     四项服务核心启动器
├─ scripts/                  启动与完整验证脚本
├─ docs/                     项目结构和 KQGIS 文档
├─ references/               原型、流程图和视觉参考
├─ 尼泊尔泥石流巨灾/         比赛方原始 GIS 数据
├─ Gis/                      KQGIS Desktop、Server 与运行数据
├─ kqgis_publish/            地图工程和发布验收图
├─ backups/                  数据库与 KQGIS 配置备份
├─ artifacts/                验收和对外交付产物
├─ licenses/                 比赛方授权文件
└─ 一键启动全部环境.cmd       Windows 双击启动入口
```

## 正式应用

- `app/backend/`：运行于 `8000`，负责管理员与组长登录、队伍、任务点位、阶段、图片和真实数据读取。
- `app/frontend/`：运行于 `5173`，包含管理员登录、智慧大屏和调度后台。
- `app/team-frontend/`：运行于 `5174`，包含组长手机号登录、任务查看、图片上传和阶段上报。
- `app/.runtime/`：自动生成的启动日志，可以在服务停止后清理旧文件。

管理员端和组长端是两个独立 Vue 项目，但共用同一个 Django 后端与数据库。

## GIS 与原始数据

- `尼泊尔泥石流巨灾/` 是比赛方原始数据，KQGIS 工程直接引用，不能移动、改名或覆盖。
- `Gis/` 包含 KQGIS 程序、已发布服务配置、缓存与日志，已发布服务依赖现有路径。
- `kqgis_publish/` 保存口岸影像、县域专题和基础地图工程及验收截图。
- `backups/` 仅用于人工恢复，不作为当前运行数据源。

## 参考与交付资料

- `references/流程图和原型图/`：界面位置和交互参考，图中示意数字不进入正式数据。
- `references/监测登录平台/`：早期登录页视觉参考。
- `references/新项目GPT快速上手资料/`：开发、数据真实性和答辩参考。
- `artifacts/组长端移动端交付包_20260926/`：供移动端开发人员使用的组长端源码、API 契约、联调说明和验收清单。
- `artifacts/组长端移动端交付包_20260926.zip`：上述交付文件夹的可发送压缩包。

## 启动与验证

双击根目录的 `一键启动全部环境.cmd`，或运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

完整验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-project.ps1
```

| 服务 | 端口 |
| --- | ---: |
| 管理员端 | 5173 |
| 组长端 | 5174 |
| Django API | 8000 |
| KQGIS Server | 9600 |

## 生成内容与维护边界

可以重新生成：两个前端的 `node_modules/`、`dist/`，Python `__pycache__/` 和停止服务后的旧运行日志。

不可随意移动：原始数据、`Gis/`、KQGIS 地图工程、SQLite 正式数据库、上传图片和授权文件。

页面数据必须来自比赛方现成资料、管理员操作或组长真实上报，不使用原型图中的示意值，也不生成未经要求的派生空间数据。
