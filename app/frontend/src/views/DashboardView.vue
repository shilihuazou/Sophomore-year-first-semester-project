<script setup>
import { computed } from "vue";
import CountyMapView from "../components/CountyMapView.vue";
import MapView from "../components/MapView.vue";
import TeamCategoryIcon from "../components/TeamCategoryIcon.vue";
import TopicCard from "../components/TopicCard.vue";

const props = defineProps({
  dashboard: { type: Object, required: true },
  markers: { type: Array, required: true },
  selectedTopicKey: { type: String, default: null },
  selectedMarkerId: { type: Number, default: null },
  groupCategories: { type: Array, required: true },
  groupAvailability: { type: Object, required: true },
  assignmentGroups: { type: Array, required: true },
});

const emit = defineEmits([
  "select-topic",
  "choose-group",
  "create-marker",
  "assign-marker",
  "delete-marker",
]);

const selectedTopic = computed(
  () =>
    props.dashboard.topics.find(
      (item) => item.key === props.selectedTopicKey,
    ) || null,
);
</script>

<template>
  <section class="dashboard-layout">
    <aside class="data-rail">
      <TopicCard
        v-for="(topic, index) in dashboard.topics"
        :key="topic.key"
        :topic="topic"
        :index="index"
        :selected="selectedTopicKey === topic.key"
        @select="emit('select-topic', $event)"
      />
    </aside>

    <section class="map-stage">
      <div class="group-strip">
        <button
          v-for="group in groupCategories"
          :key="group"
          class="group-chip"
          :aria-label="`${group}，${groupAvailability[group].available}/${groupAvailability[group].total} 支待分配，进入调度后台`"
          @click="emit('choose-group', group)"
        >
          <TeamCategoryIcon :category="group" :size="34" />
          <span class="group-chip-main">
            <span>{{ group }}</span>
            <strong
              >{{ groupAvailability[group].available }}/{{
                groupAvailability[group].total
              }}</strong
            >
          </span>
          <small>{{
            groupAvailability[group].available
              ? "待分配 · 进入后台"
              : "暂无待分配 · 进入后台"
          }}</small>
        </button>
      </div>

      <MapView
        v-if="!selectedTopic"
        :map-data="dashboard.map"
        :markers="markers"
        :assignment-groups="assignmentGroups"
        :active-marker-id="selectedMarkerId"
        @create-marker="emit('create-marker', $event)"
        @assign-marker="emit('assign-marker', $event)"
        @delete-marker="emit('delete-marker', $event)"
      />
      <CountyMapView v-else :map-data="dashboard.map" :topic="selectedTopic" />
      <button
        v-if="selectedTopic"
        class="return-port"
        @click="emit('select-topic', selectedTopic.key)"
      >
        ← 返回吉隆口岸
      </button>
    </section>
  </section>
</template>
