<script setup>
import { computed } from "vue";
import { TEAM_ICON_COLORS, TEAM_ICON_SYMBOLS } from "../config/teamIcons.js";

const props = defineProps({
  category: { type: String, required: true },
  size: { type: Number, default: 34 },
});

const symbol = computed(() => TEAM_ICON_SYMBOLS[props.category] || "");
const fill = computed(() => TEAM_ICON_COLORS[props.category] || "#526c7b");
</script>

<template>
  <svg
    class="team-category-icon"
    :width="size"
    :height="size"
    viewBox="0 0 44 44"
    role="img"
    :aria-label="`${category}图标`"
  >
    <circle cx="22" cy="22" r="20.5" :fill="fill" />
    <circle
      cx="22"
      cy="22"
      r="19.25"
      fill="none"
      stroke="white"
      stroke-opacity=".5"
      stroke-width="1.5"
    />
    <g v-html="symbol"></g>
  </svg>
</template>
