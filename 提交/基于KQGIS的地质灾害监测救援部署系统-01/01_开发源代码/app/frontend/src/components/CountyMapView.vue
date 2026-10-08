<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import Map from "ol/Map.js";
import View from "ol/View.js";
import ImageLayer from "ol/layer/Image.js";
import ImageWMS from "ol/source/ImageWMS.js";
import { defaults as defaultControls, ScaleLine } from "ol/control.js";

const props = defineProps({
  mapData: { type: Object, required: true },
  topic: { type: Object, required: true },
});
const target = ref(null);
const riverVisible = ref(false);
const coords = ref("吉隆县 · EPSG:4326");
const mapError = ref(false);
let map;
let themeSource;
let riverLayer;

function wms(layer) {
  return new ImageWMS({
    url: props.mapData.county_wms,
    params: {
      LAYERS: layer,
      VERSION: "1.1.1",
      FORMAT: "image/png",
      TRANSPARENT: true,
    },
    ratio: 1,
  });
}

function resetView() {
  if (!map) return;
  map.getView().fit(props.mapData.county_extent, {
    size: map.getSize(),
    padding: [145, 90, 65, 335],
    duration: 300,
  });
}

onMounted(() => {
  const terrainSource = wms(props.mapData.county_dem_layer);
  terrainSource.on("imageloaderror", () => {
    mapError.value = true;
  });
  themeSource = wms(props.topic.layer);
  themeSource.on("imageloaderror", () => {
    mapError.value = true;
  });
  themeSource.on("imageloadend", () => {
    mapError.value = false;
  });
  riverLayer = new ImageLayer({
    source: wms(props.mapData.county_river_layer),
    visible: false,
  });
  map = new Map({
    target: target.value,
    layers: [
      new ImageLayer({ source: terrainSource }),
      riverLayer,
      new ImageLayer({ source: themeSource }),
    ],
    view: new View({
      projection: "EPSG:4326",
      center: [85.3, 28.8],
      resolution: 0.001,
    }),
    controls: defaultControls({ attribution: true, zoom: false }).extend([
      new ScaleLine(),
    ]),
  });
  map.on("pointermove", (event) => {
    if (event.dragging) return;
    const [longitude, latitude] = event.coordinate;
    coords.value = `${longitude.toFixed(5)}° E  ·  ${latitude.toFixed(5)}° N`;
  });
  resetView();
});

watch(
  () => props.topic.layer,
  (layer) => {
    themeSource?.updateParams({ LAYERS: layer });
    mapError.value = false;
    resetView();
  },
);
watch(riverVisible, (visible) => riverLayer?.setVisible(visible));
onBeforeUnmount(() => map?.setTarget(undefined));
</script>

<template>
  <div class="map-wrap county-map">
    <div
      ref="target"
      class="map-canvas"
      :aria-label="`吉隆县${topic.label}专题地图`"
    ></div>
    <div class="map-top-label">
      <span class="live-dot"></span>吉隆县 · {{ topic.label }}
      <small>原始专题图层</small>
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
      <button title="回到县域" @click="resetView">◎</button>
    </div>
    <label class="layer-toggle"
      ><input v-model="riverVisible" type="checkbox" /> 河流水系</label
    >
    <div class="map-coords">{{ coords }} <span>EPSG:4326</span></div>
    <div v-if="mapError" class="map-error">
      吉隆县专题服务暂未加载，请检查 KQGIS Server。
    </div>
  </div>
</template>
