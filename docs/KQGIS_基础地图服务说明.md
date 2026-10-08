# KQGIS 基础地图服务说明

更新时间：2026-09-26

## 当前发布结果

- 服务名称：`jilong_base`
- 服务别名：吉隆县泥石流基础地图
- KQGIS 资源编号：`11`
- 当前状态：`running`
- 坐标系：`EPSG:4326`
- 地图范围：`84.450983, 28.2455345098, 86.158269, 29.321711`

基础服务只包含县界与河流，不包含吉隆口岸的影像细节。口岸区域另有下述独立影像服务。两项服务直接引用项目中已有的原始 Shapefile/GeoTIFF，没有生成、裁剪、重投影或计算新的空间数据；预览 PNG 只是 WMS 出图验证，不作为新数据源。

## 当前图层

| 图层 ID | 图层名称 | 原始数据 |
| --- | --- | --- |
| 1 | 基础地理（分组） | 服务图层分组 |
| 2 | 河流水系 | `尼泊尔泥石流巨灾/河流水系.shp` |
| 3 | 吉隆县边界 | `尼泊尔泥石流巨灾/吉隆县边界.shp` |

## 前端接入地址

- 地图元数据：`http://127.0.0.1:9600/kqgis/rest/services/jilong_base/map/getmetadata`
- WMS：`http://127.0.0.1:9600/kqgis/rest/services/jilong_base/map/wms`
- WMTS：`http://127.0.0.1:9600/kqgis/rest/services/jilong_base/map/wmts`
- WFS：`http://127.0.0.1:9600/kqgis/rest/services/jilong_base/data/wfs`
- KQGIS 在线预览：`http://127.0.0.1:9600/kqgis/apps/#/mapviewer?url=http://127.0.0.1:9600/kqgis/rest/services/jilong_base/map&type=tileimage&serviceType=MapService`

WMS 已通过 `GetCapabilities` 和实际 `GetMap` 请求验证，地图能够正常出图。预览图片位于 `kqgis_publish/jilong_base_preview.png`。

## 吉隆口岸与周边多时相影像服务

- 服务名称：`jilong_port_multitemporal`
- 服务别名：吉隆口岸与周边多时相影像
- 状态：已在 Server 管理界面正式发布、启用并启动
- 坐标系：服务输出 `EPSG:4326`；各原始影像仍保留自身坐标参考
- 总范围：`84.3554122795, 26.9244533837, 86.8274773613, 29.9332998416`
- 原则：直接连接项目现有 9 个 GeoTIFF，没有裁剪、重投影、分类、统计或其他空间派生

| 图层 ID | 影像 | 原始资料 |
| --- | --- | --- |
| 1 | 影像分组 | 服务图层分组 |
| 2 | 2026-08-24 Sentinel-2A SNR | `Landsat-Sentinel-中分辨率/S2A_...SAFE_SNR.tif` |
| 3 | 2026-08-26 Landsat 9 SNR PAN | `Landsat-Sentinel-中分辨率/LC09_...SNR_PAN.tif` |
| 4 | 2026-08-27 B040001100882F10 | `Vantor-高分辨率/items/B040001100882F10/B040001100882F10.tif` |
| 5 | 2026-08-27 B040001100881710 | `Vantor-高分辨率/items/B040001100881710/B040001100881710.tif` |
| 6 | 2026-08-27 B040001100881610（默认） | `Vantor-高分辨率/items/B040001100881610/B040001100881610.tif` |
| 7 | 2026-08-27 B040001100881410 | `Vantor-高分辨率/items/B040001100881410/B040001100881410.tif` |
| 8 | 2024-05-29 10300100FCB83600 | `Vantor-高分辨率/items/10300100FCB83600/10300100FCB83600.tif` |
| 9 | 2023-09-17 10500100364E8400 | `Vantor-高分辨率/items/10500100364E8400/10500100364E8400.tif` |
| 10 | 2021-10-16 10300100C86CED00 | `Vantor-高分辨率/items/10300100C86CED00/10300100C86CED00.tif` |

接入地址：

- 元数据：`http://127.0.0.1:9600/kqgis/rest/services/jilong_port_multitemporal/map/getmetadata`
- WMS：`http://127.0.0.1:9600/kqgis/rest/services/jilong_port_multitemporal/map/wms`
- KQGIS 在线预览：`http://127.0.0.1:9600/kqgis/apps/#/mapviewer?url=http://127.0.0.1:9600/kqgis/rest/services/jilong_port_multitemporal/map&type=tileimage&serviceType=MapService`

9 个栅格图层均已分别通过 WMS `GetMap` 请求验证并返回有效 PNG。旧的单景口岸服务和两项发布过程产生的重复服务已从 Server 删除；删除前的服务目录与权限库备份保存在 `backups/kqgis_before_port_collection_20260924/`。

## 发布配置

`kqgis_publish/jilong_base.kqmdx` 是 KQGIS 地图服务发布配置，只记录原始图层连接和显示结构，不包含派生空间数据。

## 吉隆县专题图服务

- 服务名称：`jilong_county_atlas`
- WMS：`http://127.0.0.1:9600/kqgis/rest/services/jilong_county_atlas/map/wms`
- 元数据：`http://127.0.0.1:9600/kqgis/rest/services/jilong_county_atlas/map/getmetadata`
- 状态：已正式发布、启动，并逐层通过 WMS GetMap 出图验证。

| 图层 ID | 内容 | 原始资料 |
| --- | --- | --- |
| 2 | 河流水系 | `河流水系.shp` |
| 3 | 历史灾害区 | 历史灾害区原始 PolygonZ Shapefile；不是灾点点位 |
| 4 | 冻土 | `吉隆县冻土.shp` |
| 5 | 2020 年冰湖 | `吉隆县冰湖_2020.shp` |
| 6 | 冰川 | `冰川.shp` |
| 7 | 县界 | `吉隆县边界.shp` |
| 8 | 原始 DEM | 吉隆县原始地形栅格 |

前端默认加载口岸独立服务；点击左侧对应资料卡时，把县域 DEM 与其专题图层作为两个 WMS 图像层叠加，避免服务器复合请求中 DEM 遮盖专题层。再次点击资料卡返回口岸。所有图层直接引用现有文件，未生成新的空间数据。
