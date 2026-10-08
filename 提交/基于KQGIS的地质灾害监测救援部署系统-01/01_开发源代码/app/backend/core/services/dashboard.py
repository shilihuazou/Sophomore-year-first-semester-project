import csv
import json
import struct

from django.conf import settings


PORT_LAYER_BY_SCENE = {
    "B040001100882F10": "4",
    "B040001100881710": "5",
    "B040001100881610": "6",
    "B040001100881410": "7",
    "10300100FCB83600": "8",
    "10500100364E8400": "9",
    "10300100C86CED00": "10",
}
DEFAULT_PORT_SCENE_ID = "B040001100881610"


def vector_record_count(shapefile):
    """Read a shapefile's existing record count from its DBF header."""
    with shapefile.with_suffix(".dbf").open("rb") as handle:
        return struct.unpack_from("<I", handle.read(8), 4)[0]


def dbf_records(shapefile):
    """Read source DBF values without aggregating or deriving new data."""
    payload = shapefile.with_suffix(".dbf").read_bytes()
    record_count, header_length, record_length = struct.unpack_from("<IHH", payload, 4)

    fields = []
    position = 32
    while payload[position] != 0x0D:
        descriptor = payload[position:position + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", errors="replace")
        fields.append((name, chr(descriptor[11]), descriptor[16]))
        position += 32

    def decode_text(raw):
        raw = raw.rstrip(b"\0 ")
        for encoding in ("utf-8", "gb18030"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin1", errors="replace")

    rows = []
    for index in range(record_count):
        record = payload[
            header_length + index * record_length:
            header_length + (index + 1) * record_length
        ]
        values = {}
        offset = 1
        for name, field_type, length in fields:
            raw = record[offset:offset + length]
            offset += length
            values[name] = (
                decode_text(raw)
                if field_type in {"C", "D"}
                else raw.decode("ascii", errors="replace").strip()
            )
        rows.append(values)
    return rows


def read_county_extent(shapefile):
    with shapefile.open("rb") as handle:
        return struct.unpack_from("<4d", handle.read(68), 36)


def read_port_scenes(root):
    scenes = []
    for item_path in sorted((root / "Vantor-高分辨率" / "items").glob("*.json")):
        item = json.loads(item_path.read_text(encoding="utf-8"))
        properties = item["properties"]
        scene_id = item["id"]
        scenes.append({
            "id": scene_id,
            "title": properties.get("title", ""),
            "datetime": properties.get("datetime"),
            "phase": properties.get("phase"),
            "cloud_cover": properties.get("eo:cloud_cover"),
            "pan_gsd": properties.get("pan_gsd"),
            "multispectral_gsd": properties.get("multispectral_gsd"),
            "bbox": item["bbox"],
            "license": item.get("license"),
            "source": f"Vantor-高分辨率/items/{item_path.name}",
            "layer": PORT_LAYER_BY_SCENE[scene_id],
            "provider": "Vantor",
            "label": f"{properties['datetime'][:10]} · {scene_id}",
        })

    active_scene = next(scene for scene in scenes if scene["id"] == DEFAULT_PORT_SCENE_ID)
    port_scenes = [active_scene]
    port_scenes.extend(
        scene for scene in sorted(scenes, key=lambda value: value["datetime"], reverse=True)
        if scene["id"] != active_scene["id"]
    )
    port_scenes.extend([
        {
            "id": "LANDSAT9_20260826_SNR_PAN",
            "label": "2026-08-26 · Landsat 9 SNR PAN",
            "datetime": "2026-08-26",
            "provider": "Landsat 9",
            "layer": "3",
            "bbox": [84.4282677174, 27.787343825, 86.8274773613, 29.9332998416],
            "source": "Landsat-Sentinel-中分辨率/LC09_L1TP_141040_20260826_20260826_02_T1_SNR_PAN.tif",
        },
        {
            "id": "SENTINEL2A_20260824_SNR",
            "label": "2026-08-24 · Sentinel-2A SNR",
            "datetime": "2026-08-24",
            "provider": "Sentinel-2A",
            "layer": "2",
            "bbox": [84.9485680624, 27.922149087, 86.0831903156, 28.9251025858],
            "source": "Landsat-Sentinel-中分辨率/S2A_MSIL2A_20260824T050231_N0512_R119_T45RUM_20260824T115710.SAFE_SNR.tif",
        },
    ])
    return active_scene, scenes, port_scenes


def build_dashboard():
    """Build dashboard JSON exclusively from original files and published layer IDs."""
    root = settings.DATA_ROOT
    lake_path = root / "吉隆县冰湖数据_1990_2020" / "吉隆县冰湖统计.csv"
    with lake_path.open("r", encoding="utf-8-sig", newline="") as handle:
        lake_rows = list(csv.DictReader(handle))

    active_scene, scenes, port_scenes = read_port_scenes(root)
    county_boundary = root / "吉隆县边界.shp"
    glacier = root / "冰川.shp"
    permafrost = root / "吉隆县冻土.shp"
    lake_2020 = root / "吉隆县冰湖数据_1990_2020" / "shapefile" / "吉隆县冰湖_2020.shp"
    historical = next((root / "西藏日喀则市吉隆县泥石流灾害区历史灾点数据").rglob("*.shp"))

    lake_row = next(row for row in lake_rows if row["year"] == "2020")
    if vector_record_count(lake_2020) != int(lake_row["lake_count"]):
        raise ValueError("2020 年冰湖统计与地图原始记录数不一致")

    glacier_names = []
    for row in dbf_records(glacier):
        name = next((value for value in row.values() if value), "")
        if name and name not in glacier_names:
            glacier_names.append(name)
        if len(glacier_names) == 4:
            break

    permafrost_rows = dbf_records(permafrost)
    historical_rows = dbf_records(historical)
    topics = [
        {
            "key": "glacier",
            "label": "冰川资料",
            "record_count": vector_record_count(glacier),
            "detail": "原始冰川图层记录数",
            "source": str(glacier.relative_to(root)),
            "layer": "6",
            "visual": {"kind": "names", "title": "原始名称字段样本", "items": glacier_names},
        },
        {
            "key": "ice_lake",
            "label": "冰湖资料 · 2020",
            "record_count": int(lake_row["lake_count"]),
            "detail": "原始统计表 lake_count；与对应地图记录数一致",
            "area_km2": lake_row["total_clip_area_km2"],
            "source": "吉隆县冰湖数据_1990_2020/吉隆县冰湖统计.csv + shapefile/吉隆县冰湖_2020.shp",
            "layer": "5",
            "visual": {
                "kind": "line",
                "title": "原始 lake_count",
                "unit": "处",
                "items": [{"label": row["year"], "value": row["lake_count"]} for row in lake_rows],
            },
        },
        {
            "key": "permafrost",
            "label": "冻土资料",
            "record_count": vector_record_count(permafrost),
            "detail": "原始冻土图层记录数",
            "source": str(permafrost.relative_to(root)),
            "layer": "4",
            "visual": {
                "kind": "bars",
                "title": "全部记录 · 原始 Shape_Area",
                "unit": "",
                "items": [
                    {"label": f"#{row['OBJECTID_1']}", "value": row["Shape_Area"], "note": row["Type"]}
                    for row in permafrost_rows
                ],
            },
        },
        {
            "key": "historical",
            "label": "历史灾害区资料",
            "record_count": vector_record_count(historical),
            "detail": "原始 PolygonZ 图层记录数；不是点位数",
            "source": str(historical.relative_to(root)),
            "layer": "3",
            "visual": {
                "kind": "bars",
                "title": "源文件前 6 条 · 原始 Area",
                "unit": "",
                "items": [
                    {"label": row["Code"], "value": row["Area"], "note": f"高程 {row['height']}"}
                    for row in historical_rows[:6]
                ],
            },
        },
    ]

    return {
        "ice_lakes": {"rows": lake_rows, "source": "吉隆县冰湖数据_1990_2020/吉隆县冰湖统计.csv"},
        "historical_sites": {
            "record_count": vector_record_count(historical),
            "source": "西藏日喀则市吉隆县泥石流灾害区历史灾点数据/*.dbf",
            "note": "数量取自原始 DBF 文件头；未进行空间分析",
        },
        "satellite": {"active": active_scene, "scenes": scenes},
        "topics": topics,
        "map": {
            "port_wms": "/kqgis/rest/services/jilong_port_multitemporal/map/wms",
            "river_wms": "/kqgis/rest/services/jilong_base/map/wms",
            "port_extent": active_scene["bbox"],
            "port_layer": active_scene["layer"],
            "port_default_scene_id": active_scene["id"],
            "port_scenes": port_scenes,
            "river_layer": "2",
            "county_wms": "/kqgis/rest/services/jilong_county_atlas/map/wms",
            "county_extent": read_county_extent(county_boundary),
            "county_dem_layer": "8",
            "county_river_layer": "2",
            "source": "Vantor-高分辨率/items/B040001100881610/B040001100881610.tif",
        },
    }
