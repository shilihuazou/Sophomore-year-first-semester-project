# KQGIS GIS 项目迁移与地图发布交接手册

> 适用对象：接手下一套 KQGIS Desktop + KQGIS Server + Vue/Django WebGIS 项目的 Codex 或开发者。  
> 依据：`D:\CangQion-Project` 中已经完成并实际生成的 KQGIS 服务配置、服务日志和前后端代码。  
> 已验证版本：KQGIS Desktop 8.5、`kqgisserver-lite-20260211_150534_release`。其他版本的界面名称和接口可能不同，操作前必须重新核对。

## 1. 给下一个 Codex 的第一原则

1. 所有地图、统计值和结论必须来自用户提供的数据，禁止编造 TIF、矢量边界、坐标、年份、图层编号或业务指标。
2. 先完整清点新项目中的 GIS 文件，再确定发布方案。不要仅根据文件名推断坐标系、范围、波段含义或 NoData 值。
3. 修改 KQGIS Server 的服务目录、管理数据库或生成配置前必须备份。
4. 优先使用 KQGIS Server 管理界面中的正式发布功能；若当前 Lite 版没有本地文件发布入口，才使用本手册中已经验证的动态创建服务接口。
5. 不要手工复制本项目的 `.srv`、`.kqmdx` 或内部数据库记录到新项目。这些文件包含绝对路径、图层结构和版本相关字段，应让新 Server 根据新数据重新生成。
6. 发布成功后必须读取新服务的元数据确定图层编号。绝对不能假定第一个业务图层永远是 `2`。

## 2. 一句话理解整条 GIS 链路

```text
本地 Shapefile / GeoTIFF
        |
        |  Desktop 检查坐标、范围、波段、NoData 和显示效果
        v
KQGIS Server 从本地文件创建 MapService
        |
        |  WMS GetMap 请求，根据 BBOX/尺寸/图层动态渲染 PNG
        v
Django（可选：代理、鉴权、缓存、透明化）
        |
        v
Vue + Leaflet 在浏览器中按瓦片请求并拼接地图
        |
        +-- GeoJSON/WFS：边界点击、高亮和属性交互
        +-- JSON/CSV API：图表、指标和业务面板
```

KQGIS Server 发布的不是一个固定 PNG，也不是把源 TIF 上传到浏览器。它发布的是一个地图网络服务。浏览器缩放或平移时，Leaflet 会不断发送带有不同地理范围 `BBOX` 的 WMS 请求，Server 再从原始 GIS 数据动态渲染一块块 PNG。

## 3. KQGIS Desktop 与 KQGIS Server 的分工

| 组件 | 作用 | 是否是浏览器运行时必需 |
| --- | --- | --- |
| KQGIS Desktop | 查看数据、检查坐标系、范围、像元/波段、NoData、叠加关系和制图样式 | 否 |
| KQGIS Server | 把本地 GIS 数据发布为 WMS/WMTS/WFS 等网络服务 | 是 |
| Django | 提供业务 API；必要时代理 KQGIS WMS、处理鉴权/CORS/透明背景 | 可选但推荐 |
| Vue | 组织页面和状态 | 是 |
| Leaflet | 创建 Web 地图、发送 WMS 瓦片请求、显示 GeoJSON、处理地图交互 | 是 |

本项目的两个现有地图服务不是由 Desktop 直接发布的，而是由 KQGIS Server 的“使用数据源直接创建服务实例”接口创建。Desktop 在这套流程中主要承担数据检查和人工预览。不要在答辩或新项目中说成“Desktop 已经发布了服务”。

## 4. 新项目收到数据后的预检查

### 4.1 文件清点

常见数据类型：

- GeoTIFF：`*.tif`、`*.tiff`，用于遥感影像、DEM、指数栅格等。
- Shapefile：至少应有同名的 `.shp`、`.shx`、`.dbf`；通常还应有 `.prj`，中文属性最好有 `.cpg`。
- CSV/Excel：通常是业务指标，不会自动变成地图；需要经纬度、行政区代码或可关联字段。
- GeoJSON：可直接给 Leaflet 使用，但数据量大时应通过后端或服务端提供。

推荐先生成数据清单，记录：

```text
文件名
文件类型
坐标系 EPSG
空间范围
波段数
像元大小
NoData 值
时间含义
属性字段
数据来源说明
```

### 4.2 用 KQGIS Desktop 检查

1. 启动 KQGIS Desktop。
2. 分别加载 Shapefile 和 GeoTIFF。
3. 查看图层属性或数据源信息，确认坐标系，不要靠肉眼猜测。
4. 检查所有图层能否在同一位置正确叠加。
5. 检查 TIF 是否有黑色背景、极端值、空值或拉伸异常。
6. 检查多波段 TIF 中每个波段的真实含义，尤其确认是否“一波段一年”。
7. 记录合理显示范围和颜色带；需要修改原始数据时先复制一份。

### 4.3 发布前必须满足的条件

- Server 进程对数据目录有读取权限。
- 数据必须位于稳定目录，发布后不要移动或改名。
- 服务名建议只用小写英文字母、数字和下划线，如 `new_project_raster`。
- 同一个地图服务中的图层尽量使用一致或可明确转换的坐标系。
- 路径传给 REST 接口时建议使用正斜杠，例如 `D:/GIS/data/a.tif`。

重要：本项目采用 `Folder` 连接方式。KQGIS Server 生成的服务配置仍然引用原始文件的绝对路径，并没有把 TIF/Shapefile 自动复制进云数据库。因此源文件必须一直存在。

## 5. 启动 KQGIS Server Lite

本项目实际启动脚本位于：

```text
D:\CangQion-Project\Gis\kqgisserver-lite-20260211_150534_release\kqwebservice\bin\start.bat
```

在脚本所在 Server 包中启动后，默认地址是：

```text
管理入口：http://127.0.0.1:9600
健康检查：http://127.0.0.1:9600/kqgis/server-manager/services/version
```

PowerShell 检查：

```powershell
Invoke-WebRequest `
  -Uri 'http://127.0.0.1:9600/kqgis/server-manager/services/version' `
  -UseBasicParsing
```

停止脚本：

```text
...\kqwebservice\bin\stop.bat
```

如果启动窗口显示 `服务已启动: http://127.0.0.1:9600`，只能说明 Server 主程序已经监听端口；仍需继续验证具体地图服务是否启动和能否出图。

## 6. 两种发布路线

### 6.1 路线 A：优先使用管理界面

不同 Lite 版本菜单可能有差异，基本目标是：

1. 登录 KQGIS Server 管理界面。
2. 进入“服务”或地图服务管理，而不是只看“数据”目录。
3. 选择新建/发布地图服务。
4. 数据源选择本地文件或文件夹连接。
5. 添加 TIF 或 Shapefile 图层。
6. 设置唯一的服务名、别名、描述和正确 EPSG。
7. 勾选 WMS；如确有需要再勾选 WMTS/WFS。
8. 创建后启用服务，并设置自动启动。
9. 打开元数据或服务预览，记录实际图层编号。

“数据”选项卡通常是数据资源目录或数据库连接目录。使用动态 `Folder` 数据源创建的地图服务不一定会显示在该目录中，但应该出现在“服务”列表中。这不是数据丢失。

### 6.2 路线 B：Lite 版没有入口时使用动态创建接口

本项目实际使用并由日志验证的接口：

```text
POST http://127.0.0.1:9600/kqgis/manager/dynamiccreateservice
```

KQGIS 对该接口的语义是“使用数据源直接创建服务实例”。下面是可复用模板。先换成一个全新的服务名测试，避免覆盖已有服务。

#### 发布一个或多个 GeoTIFF

```powershell
$baseUrl = 'http://127.0.0.1:9600/kqgis'

$body = @{
  layers = @(
    @{
      isGroupLayer = $true
      isCombined = $false
      layerName = '新项目遥感图层'
      minScale = 0
      maxScale = 0
      datasources = @(
        @{
          ConnectionInfo = @{
            connecttype = 'Folder'
            filepath = 'D:/NewProject/data/index_a.tif'
          }
          layerName = '指标A'
        },
        @{
          ConnectionInfo = @{
            connecttype = 'Folder'
            filepath = 'D:/NewProject/data/index_b.tif'
          }
          layerName = '指标B'
        }
      )
    }
  )
  serviceType = 'MapService'
  folderName = ''
  serviceName = 'new_project_raster'
  srs = 'EPSG:4326'
  aliasName = '新项目遥感服务'
  description = '由用户提供的 GeoTIFF 动态发布'
  tilePath = ''
  isDefaultTheme = 'true'
}

$json = $body | ConvertTo-Json -Depth 10
Invoke-RestMethod `
  -Method Post `
  -Uri "$baseUrl/manager/dynamiccreateservice" `
  -ContentType 'application/json; charset=utf-8' `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($json))
```

#### 发布 Shapefile

Shapefile 的连接参数与 TIF 不同：文件夹写入 `folderpath`，主文件名写入 `dataset_name`。

```powershell
$body = @{
  layers = @(
    @{
      isGroupLayer = $true
      isCombined = $false
      layerName = '新项目边界'
      minScale = 0
      maxScale = 0
      datasources = @(
        @{
          ConnectionInfo = @{
            connecttype = 'Folder'
            folderpath = 'D:/NewProject/data/boundary'
            dataset_name = 'boundary.shp'
          }
          layerName = '行政边界'
        }
      )
    }
  )
  serviceType = 'MapService'
  folderName = ''
  serviceName = 'new_project_boundary'
  srs = 'EPSG:4326'
  aliasName = '新项目边界服务'
  description = '由用户提供的 Shapefile 动态发布'
  tilePath = ''
  isDefaultTheme = 'true'
}
```

然后以与 GeoTIFF 示例相同的方式 `POST`。

接口是否需要登录令牌取决于当前 Server 配置。若匿名请求失败，应先在管理界面登录，并从该版本的官方接口说明或浏览器开发者工具中确认令牌传递方式；不要把管理员密码或长期令牌写入项目代码和文档。

### 6.3 创建后查询和启动

本版本已观察到以下管理接口：

```text
查询服务：http://127.0.0.1:9600/kqgis/manager/queryserviceinfo?servicename=服务名
服务列表：http://127.0.0.1:9600/kqgis/manager/list
启动服务：http://127.0.0.1:9600/kqgis/manager/start?servicename=服务名
```

优先在管理界面中点击“启用/启动”和“自动启动”。不要直接修改 Server 自动生成的 JSON 来代替正常管理操作。

动态创建成功后，Server 会在自己的服务目录生成类似文件：

```text
<KQMS_DATA_PATH>\gis\srvs\services\服务名.srv
<KQMS_DATA_PATH>\gis\srvs\services\服务名.kqmdx
<KQMS_DATA_PATH>\gis\srvs\services\服务名.json
```

它们分别记录服务定义、地图文档和运行设置。它们可用于排查，但不是新项目的手写输入文件。

## 7. 本项目实际发布结果，可作为对照样本

### 7.1 边界服务

```text
服务名：tuojiang_boundary
类型：MapService
坐标系：EPSG:4490（CGCS2000）
WMS：http://127.0.0.1:9600/kqgis/rest/services/tuojiang_boundary/map/wms
元数据：http://127.0.0.1:9600/kqgis/rest/services/tuojiang_boundary/map/getmetadata
图层 2：沱江流域经济带.shp
```

### 7.2 遥感服务

```text
服务名：tuojiang_remote_sensing
类型：MapService
坐标系：EPSG:4326（WGS 84）
WMS：http://127.0.0.1:9600/kqgis/rest/services/tuojiang_remote_sensing/map/wms
元数据：http://127.0.0.1:9600/kqgis/rest/services/tuojiang_remote_sensing/map/getmetadata
```

实际元数据中的图层编号：

| 图层编号 | 图层名称 | 源文件 |
| --- | --- | --- |
| `2` | NDBSI 干度指数 | `NDBSI_Tuojiang_2000_2026.tif` |
| `3` | LST 地表温度 | `LST_Tuojiang_2000_2026.tif` |
| `4` | WET 湿度指数 | `WET_Tuojiang_2000_2026.tif` |
| `5` | NDVI 植被指数 | `NDVI_Tuojiang_2000_2026.tif` |
| `6` | RSEI 生态环境质量 | `RSEI_Tuojiang_2000_2026.tif` |

这些编号只是本项目当前服务生成后的结果。新项目必须从新服务的元数据重新读取。

## 8. 验证 WMS 是否真正可用

### 8.1 先查元数据

```powershell
$service = 'new_project_raster'
Invoke-RestMethod `
  -Uri "http://127.0.0.1:9600/kqgis/rest/services/$service/map/getmetadata"
```

需要确认：

- 返回成功而不是登录页或错误 JSON。
- `status`/服务状态正常。
- 空间范围与数据真实范围一致。
- EPSG 正确。
- 图层列表、名称和编号正确。

### 8.2 用 GetMap 请求一张测试图

```text
http://127.0.0.1:9600/kqgis/rest/services/new_project_raster/map/wms
?SERVICE=WMS
&VERSION=1.1.1
&REQUEST=GetMap
&LAYERS=2
&STYLES=
&FORMAT=image/png
&TRANSPARENT=TRUE
&SRS=EPSG:4326
&BBOX=最小经度,最小纬度,最大经度,最大纬度
&WIDTH=800
&HEIGHT=600
```

实际使用时把它拼成一行 URL，并将 `LAYERS`、`SRS`、`BBOX` 替换为新服务的真实值。成功响应应满足：

- HTTP 状态为 200。
- `Content-Type` 为 `image/png`。
- 图片不是全空白、全黑或错误提示图。
- 图像空间范围与 Desktop 预览一致。

## 9. 在 Vue + Leaflet 中显示 WMS

安装 Leaflet：

```powershell
npm install leaflet
```

最小示例：

```js
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const map = L.map('map', {
  crs: L.CRS.EPSG4326,
}).setView([30.25, 104.7], 8)

L.tileLayer.wms(
  'http://127.0.0.1:9600/kqgis/rest/services/new_project_raster/map/wms',
  {
    layers: '2',
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    crs: L.CRS.EPSG4326,
    uppercase: true,
    opacity: 0.9,
  },
).addTo(map)
```

注意：

1. Leaflet 默认地图坐标系是 EPSG:3857；本项目为了匹配 KQGIS 遥感服务显式使用了 `L.CRS.EPSG4326`。
2. 新项目必须根据实际服务坐标系和 Server 的重投影能力决定 CRS，不能照抄。
3. 地图中心和缩放级别应由服务范围或 GeoJSON 的 `fitBounds` 计算，不应凭空填写。
4. `L.tileLayer.wms` 会把屏幕拆成通常为 256×256 的小块，为每块计算 BBOX 并请求 PNG，再拼成完整地图。

本项目对应实现位于：

```text
frontend/src/components/RegionMap.vue
```

核心参数为 WMS 1.1.1、PNG、透明背景、EPSG:4326，并通过 `layers` 在 `2` 到 `6` 之间切换。

## 10. 什么时候需要 Django 代理

浏览器可以直接加载 KQGIS WMS 时，不需要为了“能显示 PNG”而强行经过 Django。本项目增加代理主要是因为 KQGIS 输出的遥感图层在 NoData 区域出现近黑色背景，需要在返回浏览器前转成透明像素。

通用代理骨架：

```python
import urllib.error
import urllib.request

from django.http import HttpResponse

KQGIS_WMS = (
    "http://127.0.0.1:9600/kqgis/rest/services/"
    "new_project_raster/map/wms"
)


def kqgis_wms(request):
    query = request.META.get("QUERY_STRING", "")
    url = f"{KQGIS_WMS}?{query}" if query else KQGIS_WMS

    try:
        with urllib.request.urlopen(url, timeout=30) as upstream:
            body = upstream.read()
            content_type = upstream.headers.get("Content-Type", "image/png")
    except urllib.error.URLError as exc:
        return HttpResponse(
            str(exc.reason),
            status=502,
            content_type="text/plain; charset=utf-8",
        )

    response = HttpResponse(body, content_type=content_type)
    response["Cache-Control"] = "public, max-age=3600"
    return response
```

前端 URL 改成同源接口：

```js
L.tileLayer.wms('/api/kqgis/wms/', options).addTo(map)
```

Django 代理适合处理：

- KQGIS 服务鉴权信息，避免令牌暴露在前端。
- 浏览器跨域或生产部署的统一域名。
- NoData 透明化。
- 缓存、错误转换、日志和健康检查。

不应无条件把“黑色”当 NoData。本项目的临时算法会将 RGB 各通道都小于等于 5 的像素设为透明；若新数据中的黑色是有效值，该算法会误删真实信息。更正式的解决方案是给 GeoTIFF 正确设置 NoData/Alpha，或在 Desktop/Server 制图配置中设置透明值。

## 11. PNG 地图与鼠标交互不是一回事

WMS `GetMap` 返回的是图片，本身没有可点击的行政区属性。要实现悬停高亮、点击区县和数据面板联动，需要额外的数据层：

- GeoJSON：适合前端直接绘制中小规模边界。
- WFS：由 GIS 服务提供矢量要素和属性。
- WMS GetFeatureInfo：根据点击位置向 Server 查询要素信息。

本项目采用：

```text
KQGIS WMS PNG        负责遥感影像底图
Django GeoJSON API   负责区县形状、点击和高亮
CSV/JSON API         负责年份指标和图表
```

因此鼠标移动时 Leaflet 能把屏幕像素换算成经纬度；点击区县时真正响应事件的是上层 GeoJSON，不是下层 PNG。

## 12. 多波段 TIF 与年份切换的特别警告

本项目的 `*_2000_2026.tif` 是多波段栅格，但当前 KQGIS 服务对每个 TIF 只生成了一个 WMS 图层。现有 Vue 年份滑块会切换 CSV/GeoJSON 统计值，并不能据此宣称 WMS 栅格也切到了对应年份波段。

新项目如果需要严格的栅格时间切换，应选择并验证一种方案：

1. 把每个年份导出成独立单波段 TIF，每年作为独立 WMS 图层发布。
2. 每个年份发布成独立服务。
3. 使用 KQGIS 当前版本明确支持并经过测试的时间维度或波段参数。

在没有读取元数据和实测出图前，不得把前端年份参数描述成真实遥感影像年份切换。

## 13. 本项目遇到的问题与复用建议

| 问题 | 原因/判断 | 解决或建议 |
| --- | --- | --- |
| “数据”目录看不到已发布内容 | 动态服务直接引用 `Folder` 数据源，没有先注册到数据资源目录 | 去“服务”列表查看；用 `queryserviceinfo` 和元数据验证 |
| 动态创建后服务存在，但 REST 返回资源不存在/权限错误 | Lite 版服务实例与管理资源目录可能没有同步 | 优先在已登录的管理界面发布；检查权限和资源目录。不要直接改内部数据库 |
| 本项目曾需要同步管理资源元数据 | 当前 Lite 版兼容问题 | 当时先备份了管理库再处理；新项目不得机械复制此修复，应先保存日志并确认版本问题 |
| 遥感图层外侧为黑色 | GeoTIFF NoData 没有按透明像素输出 | 优先修正 TIF NoData/Alpha 或 Server 样式；代理透明化仅作兜底 |
| 地图错位或看不见 | EPSG、BBOX 轴顺序、范围或 Leaflet CRS 不一致 | 先用元数据和 GetMap 单独验证，再接前端 |
| 图层切换显示错内容 | 把旧项目图层编号写死 | 每次发布后重新读取元数据并建立业务 key 到图层 ID 的映射 |
| 换电脑后服务失效 | `.srv` 引用旧电脑绝对路径，或前端仍使用 `127.0.0.1` | 在新机器重新发布；局域网/服务器部署改用真实主机名、IP 或反向代理 |
| 浏览器页面正常但地图空白 | Server 未启动、具体服务未启用、WMS 请求报错 | 按“端口→服务状态→元数据→GetMap→前端网络请求”顺序排查 |

关于管理数据库：本项目曾在备份后处理过 Lite 版资源列表同步问题，但手工编辑内部 SQLite 风险很高，也不是正常发布步骤。下一个 Codex只有在管理界面和已认证 API 都无法解决、并已获得用户明确确认时，才可以研究该问题；操作前必须复制整个数据库文件，并记录每条变更。

## 14. 本地开发与正式部署差异

本地开发中：

```text
Vue：http://localhost:5173
Django：http://localhost:8000
KQGIS：http://127.0.0.1:9600
```

Vite 可以把 `/api` 代理到 Django。正式部署时建议使用 Nginx 或同类反向代理，让浏览器只访问一个公开域名：

```text
/             -> Vue 静态文件
/api/         -> Django
/kqgis/       -> KQGIS Server（或只允许 Django 访问）
```

`127.0.0.1` 永远表示“当前正在发起请求的那台机器”。其他电脑访问页面时，不能继续把 KQGIS 地址写成浏览器端的 `127.0.0.1`；应使用服务器局域网 IP、域名或通过 Django/Nginx 代理。

## 15. 新项目端到端验收清单

### 数据

- [ ] 所有 GIS 文件来自用户提供目录。
- [ ] Shapefile 组件完整，中文编码正常。
- [ ] 每个 TIF 的 EPSG、范围、波段、NoData 和时间含义已记录。
- [ ] Desktop 中叠加位置正确。

### Server

- [ ] `9600` 端口和版本接口可访问。
- [ ] 服务使用唯一英文名重新发布。
- [ ] 服务已启用并设置自动启动。
- [ ] 元数据中的范围、EPSG、图层名称和 ID 已保存。
- [ ] 每个业务图层都通过 GetMap 得到真实 PNG。
- [ ] 重启 KQGIS Server 后服务仍能恢复。

### Web

- [ ] Leaflet CRS 与 WMS 请求一致。
- [ ] 地图初始化范围来自真实数据。
- [ ] 图层选择映射到真实 WMS 图层 ID。
- [ ] 网络面板中 WMS 瓦片请求返回 200 和 `image/png`。
- [ ] 交互层明确使用 GeoJSON、WFS 或 GetFeatureInfo，不把 PNG 说成可查询矢量。
- [ ] NoData 透明化不会删除有效黑色像素。
- [ ] 页面对 Server 离线和服务错误有明确提示。

### 真实性

- [ ] 页面展示了数据来源、文件名和指标定义。
- [ ] 派生指标明确标注为派生值。
- [ ] 没有把历史遥感指标描述成实时监测。
- [ ] 没有把统计年份切换误说成栅格波段已经切换。

## 16. 可直接交给下一个 Codex 的启动提示词

```text
请先阅读项目根目录中的《KQGIS_GIS项目迁移与地图发布交接手册.md》，再开始操作。

这是一个使用 KQGIS Desktop 8.5、KQGIS Server Lite、Vue、Django 和 Leaflet 的新 WebGIS 项目。用户会提供新的 GeoTIFF、Shapefile、CSV 等数据。你必须只使用用户提供的真实数据，禁止编造任何地图、坐标、图层编号、年份、统计值或业务结论。

第一步请完整清点文件，读取每个 GIS 数据的坐标系、范围、波段数、NoData 和属性字段，并给出清单。第二步用 KQGIS Desktop 的思路检查叠加关系。第三步备份 KQGIS Server 数据目录，再优先通过管理界面发布；如果 Lite 版没有本地文件入口，可使用已经验证的 POST /kqgis/manager/dynamiccreateservice，以 Folder 数据源发布 MapService。TIF 使用 filepath，Shapefile 使用 folderpath + dataset_name。发布后必须从 getmetadata 读取真实图层 ID，并逐层用 WMS GetMap 验证。

前端使用 Leaflet 的 tileLayer.wms 展示；如有鉴权、跨域或 NoData 黑边，再通过 Django 代理。WMS PNG 只负责地图图像，点击和属性查询应使用 GeoJSON、WFS 或 GetFeatureInfo。不要复制旧项目的 .srv/.kqmdx 或内部数据库记录，不要默认图层 2，也不要默认多波段 TIF 的年份会随前端滑块切换。

每完成一个阶段，都向用户说明：使用了哪些真实文件、生成了什么服务、服务 URL、EPSG、图层 ID、验证结果，以及是否存在尚未验证的假设。
```

## 17. 本项目中可继续查阅的实现文件

```text
D:\CangQion-Project\frontend\src\components\RegionMap.vue
  Leaflet 初始化、WMS 加载、GeoJSON 交互

D:\CangQion-Project\backend\dashboard\services.py
  KQGIS 服务 URL、图层编号和本地数据配置

D:\CangQion-Project\backend\dashboard\views.py
  KQGIS 健康检查、WMS 代理和近黑 NoData 透明化

D:\CangQion-Project\scripts\start-project.ps1
  KQGIS、Django、Vue 的一键启动和健康检查

D:\CangQion-Project\Gis\kqmsdata\gis\srvs\services\tuojiang_boundary.srv
D:\CangQion-Project\Gis\kqmsdata\gis\srvs\services\tuojiang_remote_sensing.srv
  Server 实际生成的服务定义，只用于理解和核对，不要复制到新项目

D:\CangQion-Project\Gis\kqmsdata\logs\gis\log\ServiceCreate\
  服务创建时实际打开数据源的日志
```

## 18. 最终答辩式总结

本项目的 GIS 二次开发不是修改 KQGIS 内核，而是把 KQGIS Server 作为 GIS 服务底座。我们先用 Desktop 思路检查用户提供的 Shapefile 和 GeoTIFF，再让 Server 直接连接稳定的本地数据目录并生成 MapService。浏览器通过 Leaflet 按 WMS 标准请求不同范围的 PNG 瓦片，Django 负责业务接口以及必要的 WMS 代理，GeoJSON/CSV 则补充地图交互和数据面板。这样既保留了 KQGIS 的地图发布能力，也能在 Vue 智慧大屏中完成图层切换、区县交互和业务可视化。
