<script setup>
import { computed } from "vue";

const props = defineProps({
  visual: { type: Object, default: null },
});

const items = computed(() => props.visual?.items || []);
const numericItems = computed(() =>
  items.value.map((item) => ({ ...item, number: Number(item.value) })),
);
const maximum = computed(() =>
  Math.max(...numericItems.value.map((item) => item.number), 0),
);
const linePoints = computed(() => {
  const values = numericItems.value;
  if (!values.length) return "";
  const max = Math.max(...values.map((item) => item.number));
  const min = Math.min(...values.map((item) => item.number));
  const span = max - min || 1;
  return values
    .map((item, index) => {
      const x =
        values.length === 1 ? 110 : 14 + (index * 192) / (values.length - 1);
      const y = 53 - ((item.number - min) / span) * 37;
      return `${x},${y}`;
    })
    .join(" ");
});

function barHeight(value) {
  if (!maximum.value) return "4px";
  return `${Math.max(4, (Number(value) / maximum.value) * 46)}px`;
}

function displayValue(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  if (Math.abs(number) >= 100) return number.toFixed(0);
  if (Math.abs(number) >= 1) return number.toFixed(2).replace(/\.00$/, "");
  return number.toPrecision(3);
}
</script>

<template>
  <div
    v-if="visual"
    class="topic-visual"
    :aria-label="`${visual.title}，数值均来自原始文件`"
    role="img"
  >
    <div class="topic-visual-title">
      <span>{{ visual.title }}</span
      ><small>原始字段</small>
    </div>

    <div v-if="visual.kind === 'names'" class="source-name-list">
      <span v-for="name in items" :key="name">{{ name }}</span>
    </div>

    <div v-else-if="visual.kind === 'line'" class="source-line-chart">
      <svg viewBox="0 0 220 66" preserveAspectRatio="none" aria-hidden="true">
        <path d="M14 54 H206" class="chart-axis" />
        <polyline :points="linePoints" class="chart-line" />
        <circle
          v-for="(item, index) in numericItems"
          :key="item.label"
          :cx="
            numericItems.length === 1
              ? 110
              : 14 + (index * 192) / (numericItems.length - 1)
          "
          :cy="
            53 -
            ((item.number -
              Math.min(...numericItems.map((value) => value.number))) /
              (Math.max(...numericItems.map((value) => value.number)) -
                Math.min(...numericItems.map((value) => value.number)) || 1)) *
              37
          "
          r="3.5"
          class="chart-point"
        />
      </svg>
      <div class="line-value-row">
        <span v-for="item in items" :key="item.label"
          ><small>{{ item.label }}</small
          ><strong>{{ item.value }}{{ visual.unit }}</strong></span
        >
      </div>
    </div>

    <div v-else-if="visual.kind === 'bars'" class="source-bar-chart">
      <span
        v-for="item in items"
        :key="item.label"
        :title="`${item.label} · ${item.note || ''} · ${item.value}`"
      >
        <strong>{{ displayValue(item.value) }}</strong>
        <i :style="{ height: barHeight(item.value) }"></i>
        <small>{{
          item.label.replace("Q4XM-", "").replace(/^#\s*/, "#")
        }}</small>
      </span>
    </div>
  </div>
</template>
