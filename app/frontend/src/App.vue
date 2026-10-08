<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { api, patch, post, remove } from "./api.js";
import AppHeader from "./components/AppHeader.vue";
import ChangePasswordDialog from "./components/ChangePasswordDialog.vue";
import { GROUP_CATEGORIES } from "./config/teams.js";
import ConsoleView from "./views/ConsoleView.vue";
import DashboardView from "./views/DashboardView.vue";
import LoginView from "./views/LoginView.vue";

const route = ref(location.hash.slice(1) || "/login");
const user = ref(null);
const dashboard = ref(null);
const markers = ref([]);
const rescueTeams = ref([]);
const selectedMarker = ref(null);
const selectedTopicKey = ref(null);
const activeGroup = ref("");
const activeTeam = ref("");
const busy = ref(true);
const error = ref("");
const notice = ref("");
const passwordDialogOpen = ref(false);
const passwordBusy = ref(false);
const passwordError = ref("");
const teamBusy = ref(false);
const teamError = ref("");
let refreshTimer;
let noticeTimer;

const assignmentGroups = computed(() =>
  rescueTeams.value.map((team) => team.name),
);

const groupAvailability = computed(() => {
  const occupiedTeams = new Set(
    markers.value
      .filter((marker) => marker.group && marker.status !== "已完成")
      .map((marker) => marker.group),
  );
  return Object.fromEntries(
    GROUP_CATEGORIES.map((category) => {
      const teams = rescueTeams.value.filter(
        (team) => team.category === category,
      );
      return [
        category,
        {
          total: teams.length,
          available: teams.filter(
            (team) => team.status === "上线" && !occupiedTeams.has(team.name),
          ).length,
        },
      ];
    }),
  );
});

watch(notice, (message) => {
  window.clearTimeout(noticeTimer);
  if (message) {
    noticeTimer = window.setTimeout(() => {
      notice.value = "";
    }, 3000);
  }
});

function syncRoute() {
  route.value = location.hash.slice(1) || "/login";
}

function go(path) {
  location.hash = path;
  route.value = path;
  error.value = "";
}

function toggleTopic(key) {
  selectedTopicKey.value = selectedTopicKey.value === key ? null : key;
}

function startOperationalRefresh() {
  window.clearInterval(refreshTimer);
  refreshTimer = window.setInterval(
    () => refreshOperationalData().catch(() => {}),
    10000,
  );
}

async function loadData() {
  const [sourceData, markerData, teamData] = await Promise.all([
    api("/dashboard/"),
    api("/markers/"),
    api("/rescue-teams/"),
  ]);
  dashboard.value = sourceData;
  markers.value = markerData.markers;
  rescueTeams.value = teamData.teams;
  syncSelectedMarker();
}

async function refreshOperationalData() {
  if (!user.value) return;
  const [markerData, teamData] = await Promise.all([
    api("/markers/"),
    api("/rescue-teams/"),
  ]);
  markers.value = markerData.markers;
  rescueTeams.value = teamData.teams;
  syncSelectedMarker();
}

function syncSelectedMarker() {
  if (!selectedMarker.value) return;
  selectedMarker.value =
    markers.value.find((item) => item.id === selectedMarker.value.id) || null;
}

onMounted(async () => {
  window.addEventListener("hashchange", syncRoute);
  try {
    await api("/csrf/");
    user.value = (await api("/me/")).user;
    await loadData();
    startOperationalRefresh();
    if (route.value === "/login") go("/dashboard");
  } catch {
    user.value = null;
    go("/login");
  } finally {
    busy.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener("hashchange", syncRoute);
  window.clearInterval(refreshTimer);
  window.clearTimeout(noticeTimer);
});

async function signIn(credentials) {
  error.value = "";
  busy.value = true;
  try {
    user.value = (await post("/login/", credentials)).user;
    await loadData();
    startOperationalRefresh();
    go("/dashboard");
  } catch (err) {
    error.value = err.message;
  } finally {
    busy.value = false;
  }
}

async function signOut() {
  try {
    await post("/logout/", {});
  } finally {
    window.clearInterval(refreshTimer);
    user.value = null;
    dashboard.value = null;
    markers.value = [];
    rescueTeams.value = [];
    selectedMarker.value = null;
    selectedTopicKey.value = null;
    passwordDialogOpen.value = false;
    go("/login");
  }
}

function openPasswordDialog() {
  passwordError.value = "";
  passwordDialogOpen.value = true;
}

function closePasswordDialog() {
  if (passwordBusy.value) return;
  passwordError.value = "";
  passwordDialogOpen.value = false;
}

async function changePassword(payload) {
  passwordError.value = "";
  passwordBusy.value = true;
  try {
    await post("/change-password/", payload);
    passwordDialogOpen.value = false;
    notice.value = "密码修改成功，下次登录请使用新密码。";
  } catch (err) {
    passwordError.value = err.message;
  } finally {
    passwordBusy.value = false;
  }
}

async function createMarker(coordinate) {
  error.value = "";
  try {
    const response = await post("/markers/", coordinate);
    await refreshOperationalData();
    selectedMarker.value = response.marker;
    notice.value = `标记点 #${response.marker.id} 已保存，请选择救援组。`;
  } catch (err) {
    error.value = err.message;
  }
}

async function assignMarker({ marker, group }) {
  if (!marker || !group) return;
  try {
    const response = await patch(`/markers/${marker.id}/`, { group });
    await refreshOperationalData();
    selectedMarker.value = response.marker;
    notice.value = `已分配，任务编号 ${response.marker.task_number}，状态自动变为“执行中”。`;
  } catch (err) {
    error.value = err.message;
  }
}

async function deleteMarker(marker) {
  if (!marker) return;
  try {
    await remove(`/markers/${marker.id}/`);
    if (selectedMarker.value?.id === marker.id) selectedMarker.value = null;
    await refreshOperationalData();
    notice.value = `标记点 #${marker.id} 已删除。`;
  } catch (err) {
    error.value = err.message;
  }
}

function chooseGroup(group) {
  activeGroup.value = group;
  activeTeam.value =
    rescueTeams.value.find((team) => team.category === group)?.name || "";
  selectedMarker.value = null;
  go("/console");
}

function selectTeam(team) {
  activeTeam.value = team.name;
  activeGroup.value = team.category;
}

async function createTeam(payload) {
  teamError.value = "";
  teamBusy.value = true;
  try {
    const response = await post("/rescue-teams/", payload);
    await refreshOperationalData();
    activeGroup.value = response.team.category;
    activeTeam.value = response.team.name;
    notice.value = `${response.team.name} 已新增，大屏队伍数量已同步更新。`;
  } catch (err) {
    teamError.value = err.message;
  } finally {
    teamBusy.value = false;
  }
}

async function updateTeam({ id, values }) {
  teamError.value = "";
  teamBusy.value = true;
  try {
    const response = await patch(`/rescue-teams/${id}/`, values);
    await refreshOperationalData();
    activeGroup.value = response.team.category;
    activeTeam.value = response.team.name;
    notice.value = `${response.team.name} 的资料已保存。`;
  } catch (err) {
    teamError.value = err.message;
  } finally {
    teamBusy.value = false;
  }
}

async function deleteTeam(team) {
  teamError.value = "";
  teamBusy.value = true;
  try {
    await remove(`/rescue-teams/${team.id}/`);
    if (activeTeam.value === team.name) activeTeam.value = "";
    await refreshOperationalData();
    notice.value = `${team.name} 已删除，大屏队伍数量已同步更新。`;
  } catch (err) {
    teamError.value = err.message;
  } finally {
    teamBusy.value = false;
  }
}
</script>

<template>
  <div v-if="busy && !user" class="boot-screen">正在连接吉隆口岸数据服务…</div>
  <LoginView
    v-else-if="!user || route === '/login'"
    :busy="busy"
    :error="error"
    @submit="signIn"
  />
  <div
    v-else
    class="app-shell"
    :class="{ 'console-route': route === '/console' }"
  >
    <AppHeader @change-password="openPasswordDialog" @sign-out="signOut" />
    <ChangePasswordDialog
      v-if="passwordDialogOpen"
      :busy="passwordBusy"
      :error="passwordError"
      @close="closePasswordDialog"
      @submit="changePassword"
    />
    <div
      v-if="notice"
      class="toast"
      role="status"
      aria-live="polite"
      @click="notice = ''"
    >
      {{ notice }} <span>×</span>
    </div>
    <div v-if="error" class="error-banner" @click="error = ''">
      {{ error }} <span>×</span>
    </div>

    <DashboardView
      v-if="route === '/dashboard' && dashboard"
      :dashboard="dashboard"
      :markers="markers"
      :selected-topic-key="selectedTopicKey"
      :selected-marker-id="selectedMarker?.id ?? null"
      :group-categories="GROUP_CATEGORIES"
      :group-availability="groupAvailability"
      :assignment-groups="assignmentGroups"
      @select-topic="toggleTopic"
      @choose-group="chooseGroup"
      @create-marker="createMarker"
      @assign-marker="assignMarker"
      @delete-marker="deleteMarker"
    />
    <ConsoleView
      v-else-if="route === '/console'"
      :active-group="activeGroup"
      :active-team="activeTeam"
      :categories="GROUP_CATEGORIES"
      :rescue-teams="rescueTeams"
      :busy="teamBusy"
      :error="teamError"
      @back="go('/dashboard')"
      @select-team="selectTeam"
      @clear-team-error="teamError = ''"
      @create-team="createTeam"
      @update-team="updateTeam"
      @delete-team="deleteTeam"
    />
  </div>
</template>
