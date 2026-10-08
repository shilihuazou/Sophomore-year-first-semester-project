# 吉隆口岸泥石流监测与救援调度

Vue 3 + OpenLayers + Django 5 + 本机 KQGIS Server。界面参照 `../references/流程图和原型图/` 最新原型：白色顶栏、左侧四张数据卡、中央实景地图、上方五个救援组入口以及浅色后台。原型中的数字、人员、P1–P5 点位均不作为真实数据导入。

## 启动

Windows 下可直接双击项目根目录的 `一键启动全部环境.cmd`。脚本会检查并安装缺失依赖、执行数据库迁移、启动管理员端、组长端、Django 与 KQGIS，并自动打开两个前端页面。

本机已经安装依赖后，可以一键在后台启动前端、后端和 KQGIS：

```powershell
powershell -ExecutionPolicy Bypass -File D:\CangQiongPj\scripts\start.ps1
```

脚本会检查现有端口，跳过已经运行的服务，并验证页面响应。启动日志保存在 `app/.runtime/`；后台进程运行期间不需要保留终端窗口。重启电脑后重新运行脚本。

手动启动方式如下：

先启动 KQGIS Server 9600 端口的 `jilong_port_multitemporal`、`jilong_county_atlas` 和 `jilong_base` 服务。然后在两个终端运行：

```powershell
cd D:\CangQiongPj\app\backend
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py seed_demo
py manage.py runserver 127.0.0.1:8000
```

```powershell
cd D:\CangQiongPj\app\frontend
npm install
npm run dev
```

```powershell
cd D:\CangQiongPj\app\team-frontend
npm install
npm run dev
```

管理员端本机地址为 `http://127.0.0.1:5173/#/login`，组长端本机地址为 `http://127.0.0.1:5174/`。一键启动脚本还会输出当前电脑的局域网访问地址；公网域名、HTTPS 与端口映射说明见 [`../docs/NETWORK_ACCESS.md`](../docs/NETWORK_ACCESS.md)。应用管理员账号为 `admin`；当前密码按项目所有者要求设置。登录后可通过右上角“修改密码”校验原密码并更新密码，成功后当前会话保持登录。`seed_demo` 仅在首次创建时打印随机密码，重复运行不改密码。以前生成的队长演示账号不会通过当前管理员端登录验证。

## 地图与标记

- 默认是吉隆口岸影像，地图左上角可在项目现有的 9 景 Vantor、Landsat、Sentinel 影像间切换；选择后自动定位到该景原始覆盖范围。管理员单击任一已发布影像范围内地图，创建一个持久化的“待分配”水滴点。鼠标靠近点位出现分配按钮。
- 地图上方五个按钮是救援类别入口，点击任意一个直接进入该类别的调度后台；比例为“上线且无未完成任务的队伍数 / 该类别全部队伍数”。队伍状态或任务占用变化后立即重新计算。页头不再保留重复的“大屏/后台”切换。
- 具体队伍完全由数据库管理；截至 2026-09-26，后台保留 6 支具体队伍，分属抢险救援、医疗治疗、电力保障、地质监测和群众安置五个类别。管理员可继续新增、修改或删除未被任务引用的队伍。
- 未分配点位在鼠标靠近或点击后，于标记旁显示紧凑分配表单；选择具体队伍并确认后状态自动为“执行中”。未分配点保持红色水滴，执行中点位变为对应类别的红底圆形矢量图标，完成后变为绿底同类图标。
- 每个标记浮窗都提供“删除标记”，需在原位二次确认后才会删除点位及其上报记录；取消确认不会改变现有数据。
- 组长任务端负责录入任务阶段与现场图片。大屏每 10 秒读取一次标记数据，悬停或点击点位可查看任务编号、图片和进度。
- 调度后台按原型提供五类救援队伍的树形管理表格，可新增、查看、编辑基础资料和删除未被任务引用的队伍；状态仅在左侧只读展示，不允许在详情表单或管理接口中手动修改。变更会立即同步到大屏数量与点位分配下拉框，并每 10 秒自动复核。
- 组长任务端运行于 `http://127.0.0.1:5174/`，使用调度后台登记的组长手机号和默认密码 `123` 登录。管理员分配点位时自动生成唯一任务编号；阶段依次为“未分配”“已分配任务，请尽快到达（0%）”“任务中（50%）”“任务完成（100%）”，组长可上传现场图片或上报下一阶段，任务进度和图片会同步显示在管理员大屏点位卡片中。
- 组长端从“已分配任务，请尽快到达（0%）”上报为“任务中（50%）”，再次上报为“任务完成（100%）”；完成后点位变绿。图片也可以单独上传而不推进阶段。
- 左侧四卡的数量均来自原始 CSV/DBF，并直接展示原始字段：冰湖为 1990/2020 `lake_count` 折线，冻土为全部 7 条 `Shape_Area` 柱形，历史灾害区为源文件前 6 条 `Area` 柱形，冰川展示原始名称样本。点击切换到相应吉隆县专题图，再次点击返回口岸。没有计算总量、均值、增幅、风险等级或其他派生指标。

## 接口契约

管理员端使用 Django 管理员会话；组长端使用独立的救援组会话键。两端都使用 CSRF Cookie，不开放匿名读写。

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/csrf/` | 设置 CSRF Cookie |
| POST | `/api/login/` | JSON `{"username":"…","password":"…"}` |
| GET/POST | `/api/rescue-teams/` | 读取或新增救援队伍；仅管理员可用 |
| GET/PATCH/DELETE | `/api/rescue-teams/{id}/` | 查看、修改或删除尚未被点位任务引用的队伍 |
| GET | `/api/markers/` | 读取所有标记和上报记录 |
| POST | `/api/markers/` | 管理员创建点位，JSON 经纬度；手机端无需调用 |
| PATCH | `/api/markers/{id}/` | 管理员分配具体队伍，JSON `{"group":"抢险救援一组"}`；手机端无需调用 |
| DELETE | `/api/markers/{id}/` | 管理员删除点位；同时删除该点位的上报记录和已上传图片 |
| POST | `/api/markers/{id}/reports/` | `multipart/form-data`：`content`、`progress`（0–100）、`completed`（`true`/`false`）、可选 `photo`（JPEG/PNG/WebP，≤10 MB） |
| GET | `/api/marker-reports/{id}/photo/` | 管理员或对应被分配队伍组长查看图片 |
| POST | `/api/team-portal/login/` | 组长手机号与密码登录；新队伍默认密码为 `123` |
| POST | `/api/team-portal/logout/` | 退出组长端，不影响管理员会话 |
| GET | `/api/team-portal/me/` | 返回当前组长所属队伍 |
| GET | `/api/team-portal/tasks/` | 返回该队伍的当前及近期任务 |
| POST | `/api/team-portal/tasks/{id}/report/` | `multipart/form-data`：`advance` 与可选 `photo`；推进阶段或单独上传图片 |

上报前标记必须处于“执行中”，并且只能由被分配队伍的组长操作。接口返回更新后的 `marker`，其中 `reports[].photo_url` 可供管理员或对应组长会话展示。

本机版本不表示实时监测或真实救援部署。正式部署需配置 `DJANGO_SECRET_KEY`、关闭 DEBUG、启用 HTTPS 并审查图片访问权限。
