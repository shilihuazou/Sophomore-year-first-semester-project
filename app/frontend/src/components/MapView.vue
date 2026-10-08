<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Map from "ol/Map.js";
import View from "ol/View.js";
import ImageLayer from "ol/layer/Image.js";
import VectorLayer from "ol/layer/Vector.js";
import ImageWMS from "ol/source/ImageWMS.js";
import VectorSource from "ol/source/Vector.js";
import Feature from "ol/Feature.js";
import Point from "ol/geom/Point.js";
import { Icon, Style } from "ol/style.js";
import { defaults as defaultControls, ScaleLine } from "ol/control.js";
import { resolveTeamCategory, TEAM_ICON_SYMBOLS } from "../config/teamIcons.js";

const props = defineProps({
  mapData: { type: Object, required: true },
  markers: { type: Array, default: () => [] },
  assignmentGroups: { type: Array, default: () => [] },
  activeMarkerId: { type: Number, default: null },
});
const emit = defineEmits(["create-marker", "assign-marker", "delete-marker"]);
const target = ref(null);
const riverVisible = ref(false);
const coords = ref("85.379° E  ·  28.277° N");
const mapError = ref(false);
const hovered = ref(null);
const popover = ref(null);
const popupGroup = ref("");
const popupPinned = ref(false);
const confirmDeleteId = ref(null);
const popupPosition = ref({ left: "0px", top: "0px" });
const scenes = computed(() =>
  props.mapData.port_scenes?.length
    ? props.mapData.port_scenes
    : [
        {
          id: "default",
          label: "吉隆口岸影像",
          layer: props.mapData.port_layer,
          bbox: props.mapData.port_extent,
          provider: "Vantor",
        },
      ],
);
const selectedSceneId = ref(
  props.mapData.port_default_scene_id || scenes.value[0].id,
);
const activeScene = computed(
  () =>
    scenes.value.find((scene) => scene.id === selectedSceneId.value) ||
    scenes.value[0],
);
let map;
let imageSource;
let riverLayer;
let vectorSource;
let hidePopupTimer;

function markerStyle(marker) {
  const unassigned = marker.status === "待分配";
  const category = resolveTeamCategory(marker.group);
  const fill = marker.status === "已完成" ? "#26a269" : "#d74749";
  const svg = unassigned
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="42" height="52" viewBox="0 0 42 52"><path d="M21 2C10.5 2 3 9.7 3 20c0 13 18 29 18 29s18-16 18-29C39 9.7 31.5 2 21 2Z" fill="#d74749" stroke="white" stroke-width="2.5"/><circle cx="21" cy="20" r="13" fill="white" fill-opacity=".16"/><circle cx="21" cy="20" r="5" fill="white"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="46" height="46" viewBox="0 0 44 44"><circle cx="22" cy="22" r="20" fill="${fill}" stroke="white" stroke-width="2.5"/><circle cx="22" cy="22" r="16.5" fill="white" fill-opacity=".08"/>${TEAM_ICON_SYMBOLS[category] || ""}</svg>`;
  return new Style({
    image: new Icon({
      src: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,
      anchor: unassigned ? [0.5, 0.94] : [0.5, 0.5],
    }),
  });
}
function syncMarkers() {
  if (!vectorSource) return;
  vectorSource.clear();
  for (const marker of props.markers) {
    const feature = new Feature(new Point([marker.longitude, marker.latitude]));
    feature.set("marker", marker);
    feature.setStyle(markerStyle(marker));
    vectorSource.addFeature(feature);
  }
  if (hovered.value)
    hovered.value =
      props.markers.find((item) => item.id === hovered.value.id) || null;
}
function resetView() {
  if (!map || !activeScene.value?.bbox) return;
  map.getView().fit(activeScene.value.bbox, {
    padding: [160, 55, 80, 310],
    duration: 350,
  });
}
function hoverMarker(event) {
  const feature = map.forEachFeatureAtPixel(
    event.pixel,
    (candidate) => candidate,
    { hitTolerance: 8 },
  );
  const marker = feature?.get("marker") || null;
  target.value.style.cursor = marker ? "pointer" : "crosshair";
  if (marker) {
    window.clearTimeout(hidePopupTimer);
    if (marker.status === "待分配" && hovered.value?.id !== marker.id)
      popupGroup.value = "";
    if (hovered.value?.id !== marker.id) confirmDeleteId.value = null;
    hovered.value = marker;
    const pixel = map.getPixelFromCoordinate([
      marker.longitude,
      marker.latitude,
    ]);
    positionPopup(pixel);
  } else if (!popupPinned.value) {
    window.clearTimeout(hidePopupTimer);
    hidePopupTimer = window.setTimeout(() => {
      if (!popupPinned.value) hovered.value = null;
    }, 450);
  }
}
function positionPopup(pixel) {
  const [width, height] = map.getSize();
  popupPosition.value = {
    left: `${Math.max(8, Math.min(pixel[0] + 19, width - 245))}px`,
    top: `${Math.max(8, Math.min(pixel[1] - 76, height - 225))}px`,
  };
}
function showMarker(marker) {
  if (!map || !marker) return;
  window.clearTimeout(hidePopupTimer);
  hovered.value = marker;
  confirmDeleteId.value = null;
  popupGroup.value = marker.group || "";
  const pixel = map.getPixelFromCoordinate([marker.longitude, marker.latitude]);
  positionPopup(pixel);
}
function focusActiveMarker() {
  const marker = props.markers.find((item) => item.id === props.activeMarkerId);
  if (marker) requestAnimationFrame(() => showMarker(marker));
}
function assignHovered() {
  if (!hovered.value || !popupGroup.value) return;
  emit("assign-marker", { marker: hovered.value, group: popupGroup.value });
}
function keepPopup() {
  popupPinned.value = true;
  window.clearTimeout(hidePopupTimer);
}
function schedulePopupClose() {
  window.clearTimeout(hidePopupTimer);
  hidePopupTimer = window.setTimeout(() => {
    if (popover.value?.contains(document.activeElement)) return;
    closePopup();
  }, 700);
}
function closePopup() {
  popupPinned.value = false;
  confirmDeleteId.value = null;
  hovered.value = null;
}
function requestDelete() {
  if (!hovered.value) return;
  if (confirmDeleteId.value !== hovered.value.id) {
    confirmDeleteId.value = hovered.value.id;
    return;
  }
  emit("delete-marker", hovered.value);
}
onMounted(() => {
  imageSource = new ImageWMS({
    url: props.mapData.port_wms,
    params: {
      LAYERS: activeScene.value.layer,
      VERSION: "1.1.1",
      FORMAT: "image/png",
      TRANSPARENT: false,
    },
    ratio: 1,
    attributions: "Vantor Open Data · CC BY-NC 4.0",
  });
  imageSource.on("imageloaderror", () => {
    mapError.value = true;
  });
  imageSource.on("imageloadend", () => {
    mapError.value = false;
  });
  riverLayer = new ImageLayer({
    visible: false,
    opacity: 0.8,
    source: new ImageWMS({
      url: props.mapData.river_wms,
      params: {
        LAYERS: props.mapData.river_layer,
        VERSION: "1.1.1",
        FORMAT: "image/png",
        TRANSPARENT: true,
      },
      ratio: 1,
    }),
  });
  vectorSource = new VectorSource();
  map = new Map({
    target: target.value,
    layers: [
      new ImageLayer({ source: imageSource }),
      riverLayer,
      new VectorLayer({ source: vectorSource }),
    ],
    view: new View({
      projection: "EPSG:4326",
      center: [85.379735, 28.276811],
      resolution: 0.000028,
    }),
    controls: defaultControls({ attribution: true, zoom: false }).extend([
      new ScaleLine(),
    ]),
  });
  map.on("pointermove", (event) => {
    if (event.dragging) return;
    const [longitude, latitude] = event.coordinate;
    coords.value = `${longitude.toFixed(5)}° E  ·  ${latitude.toFixed(5)}° N`;
    hoverMarker(event);
  });
  map.on("singleclick", (event) => {
    const feature = map.forEachFeatureAtPixel(
      event.pixel,
      (candidate) => candidate,
      { hitTolerance: 8 },
    );
    if (feature?.get("marker")) showMarker(feature.get("marker"));
    else
      emit("create-marker", {
        longitude: event.coordinate[0],
        latitude: event.coordinate[1],
      });
  });
  syncMarkers();
  focusActiveMarker();
});
watch(() => props.markers, syncMarkers, { deep: true });
watch(() => props.activeMarkerId, focusActiveMarker);
watch(riverVisible, (visible) => riverLayer?.setVisible(visible));
watch(selectedSceneId, () => {
  mapError.value = false;
  hovered.value = null;
  imageSource?.updateParams({
    LAYERS: activeScene.value.layer,
    _scene: activeScene.value.id,
  });
  resetView();
});
onBeforeUnmount(() => {
  window.clearTimeout(hidePopupTimer);
  map?.setTarget(undefined);
});
</script>

<template>
  <div class="map-wrap">
    <div
      ref="target"
      class="map-canvas"
      aria-label="吉隆口岸遥感影像地图；单击地图新增标记点"
    ></div>
    <div
      v-if="hovered"
      ref="popover"
      class="marker-popover"
      :style="popupPosition"
      @mouseenter="keepPopup"
      @mouseleave="schedulePopupClose"
      @focusin="keepPopup"
      @focusout="schedulePopupClose"
    >
      <div class="marker-popover-head">
        <strong>{{ hovered.task_number || `标记点 #${hovered.id}` }}</strong
        ><button type="button" aria-label="关闭点位卡片" @click="closePopup">
          ×
        </button>
      </div>
      <span>{{ hovered.group || "待分配" }} · {{ hovered.status }}</span>
      <span v-if="hovered.group"
        >{{ hovered.stage_label }} · 任务进度 {{ hovered.progress }}%</span
      >
      <img
        v-if="hovered.reports?.find((report) => report.photo_url)"
        :src="hovered.reports.find((report) => report.photo_url).photo_url"
        alt="现场上报图片"
      />
      <form
        v-if="hovered.status === '待分配'"
        class="marker-quick-assign"
        @submit.prevent="assignHovered"
      >
        <select
          v-model="popupGroup"
          aria-label="选择救援队伍"
          required
          @pointerdown="keepPopup"
          @change="keepPopup"
        >
          <option value="" disabled>选择救援队伍</option>
          <option v-for="group in assignmentGroups" :key="group" :value="group">
            {{ group }}
          </option>
        </select>
        <button type="submit">确认分配</button>
      </form>
      <span v-else-if="hovered.status === '执行中' && !hovered.reports?.length"
        >等待手机端上报图片与进度</span
      >
      <div class="marker-delete-row">
        <span v-if="confirmDeleteId === hovered.id">确认删除此标记点？</span>
        <button
          v-if="confirmDeleteId === hovered.id"
          type="button"
          class="marker-delete-cancel"
          @click="confirmDeleteId = null"
        >
          取消
        </button>
        <button
          type="button"
          class="marker-delete-button"
          @click="requestDelete"
        >
          {{ confirmDeleteId === hovered.id ? "确认删除" : "删除标记" }}
        </button>
      </div>
    </div>
    <div class="map-top-label imagery-picker">
      <div>
        <span class="live-dot"></span> 吉隆口岸与周边 · 现有影像
        <small>共 {{ scenes.length }} 景</small>
      </div>
      <select v-model="selectedSceneId" aria-label="选择吉隆口岸及周边影像">
        <option v-for="scene in scenes" :key="scene.id" :value="scene.id">
          {{ scene.label }}
        </option>
      </select>
      <small
        >{{ activeScene.provider }} · 图层 {{ activeScene.layer }} ·
        单击地图落点</small
      >
    </div>
    <div class="map-tools">
      <button
        title="放大"
        @click="
          map?.getView().setResolution(map.getView().getResolution() / 1.6)
        "
      >
        ＋
      </button>
      <button
        title="缩小"
        @click="
          map?.getView().setResolution(map.getView().getResolution() * 1.6)
        "
      >
        －
      </button>
      <button title="查看当前整景范围" @click="resetView">◎</button>
    </div>
    <label class="layer-toggle"
      ><input v-model="riverVisible" type="checkbox" /> 河流水系</label
    >
    <div class="map-coords">{{ coords }} <span>EPSG:4326</span></div>
    <div v-if="mapError" class="map-error">
      KQGIS 影像暂未加载，请检查 9600 端口的服务状态。
    </div>
  </div>
</template>
