<script setup>
import TopicMiniChart from "./TopicMiniChart.vue";

defineProps({
  topic: { type: Object, required: true },
  index: { type: Number, required: true },
  selected: { type: Boolean, default: false },
});

defineEmits(["select"]);

const symbols = ["◆", "◈", "▧", "⌁"];
</script>

<template>
  <button
    class="data-card topic-card"
    :class="[`topic-${index}`, { selected }]"
    :aria-pressed="selected"
    @click="$emit('select', topic.key)"
  >
    <span class="card-head">
      <span class="card-symbol">{{ symbols[index] }}</span>
      <span>{{ topic.label }}</span>
      <small>{{ selected ? "返回口岸 ↩" : "查看县域图 →" }}</small>
    </span>
    <span class="large-metric">
      {{ topic.record_count }}
      <small>{{ topic.key === "ice_lake" ? "处" : "条记录" }}</small>
    </span>
    <span class="metric-sub">{{ topic.detail }}</span>
    <span v-if="topic.area_km2" class="fact-row">
      <span>原始表面积字段 km²</span>
      <strong class="compact-value">{{ topic.area_km2 }}</strong>
    </span>
    <TopicMiniChart :visual="topic.visual" />
    <span class="source-line">来源：{{ topic.source }}</span>
  </button>
</template>
