<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { api, post } from "./api.js";

const booting = ref(true);
const busy = ref(false);
const team = ref(null);
const tasks = ref([]);
const selectedTaskId = ref(null);
const phone = ref("");
const password = ref("");
const photo = ref(null);
const photoInput = ref(null);
const error = ref("");
const notice = ref("");
let refreshTimer;
let noticeTimer;

const activeTasks = computed(() =>
  tasks.value.filter((task) => task.status === "执行中"),
);
const selectedTask = computed(
  () =>
    activeTasks.value.find((task) => task.id === selectedTaskId.value) ||
    activeTasks.value[0] ||
    null,
);
const completedTasks = computed(() =>
  tasks.value.filter((task) => task.status === "已完成").slice(0, 5),
);
const latestPhoto = computed(() =>
  selectedTask.value?.reports?.find((report) => report.photo_url),
);
const advanceButtonText = computed(() =>
  selectedTask.value?.current_stage >= 2 ? "上报任务完成" : "上报下一阶段",
);

watch(notice, (message) => {
  window.clearTimeout(noticeTimer);
  if (message) {
    noticeTimer = window.setTimeout(() => (notice.value = ""), 3000);
  }
});

function selectCurrentTask() {
  if (!activeTasks.value.length) {
    selectedTaskId.value = null;
    return;
  }
  if (!activeTasks.value.some((task) => task.id === selectedTaskId.value)) {
    selectedTaskId.value = activeTasks.value[0].id;
  }
}

async function loadTasks() {
  const result = await api("/team-portal/tasks/");
  team.value = result.team;
  tasks.value = result.tasks;
  selectCurrentTask();
}

function startRefresh() {
  window.clearInterval(refreshTimer);
  refreshTimer = window.setInterval(() => loadTasks().catch(() => {}), 10000);
}

onMounted(async () => {
  try {
    await api("/csrf/");
    team.value = (await api("/team-portal/me/")).team;
    await loadTasks();
    startRefresh();
  } catch (err) {
    if (err.status !== 401) error.value = err.message;
    team.value = null;
  } finally {
    booting.value = false;
  }
});

onUnmounted(() => {
  window.clearInterval(refreshTimer);
  window.clearTimeout(noticeTimer);
});

async function signIn() {
  error.value = "";
  busy.value = true;
  try {
    team.value = (
      await post("/team-portal/login/", {
        phone: phone.value,
        password: password.value,
      })
    ).team;
    password.value = "";
    await loadTasks();
    startRefresh();
  } catch (err) {
    error.value = err.message;
  } finally {
    busy.value = false;
  }
}

async function signOut() {
  try {
    await post("/team-portal/logout/", {});
  } finally {
    window.clearInterval(refreshTimer);
    team.value = null;
    tasks.value = [];
    selectedTaskId.value = null;
    photo.value = null;
    error.value = "";
  }
}

function choosePhoto(event) {
  photo.value = event.target.files?.[0] || null;
}

async function submitReport(shouldAdvance) {
  if (!selectedTask.value) return;
  error.value = "";
  busy.value = true;
  try {
    const body = new FormData();
    body.append("advance", String(shouldAdvance));
    if (photo.value) body.append("photo", photo.value);
    await api(`/team-portal/tasks/${selectedTask.value.id}/report/`, {
      method: "POST",
      body,
    });
    const message = shouldAdvance
      ? "任务阶段已更新，大屏将同步显示最新进度。"
      : "现场图片已上传，大屏将同步显示。";
    photo.value = null;
    if (photoInput.value) photoInput.value.value = "";
    await loadTasks();
    notice.value = message;
  } catch (err) {
    error.value = err.message;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main v-if="booting" class="boot-screen">正在连接任务服务…</main>

  <main v-else-if="!team" class="login-page">
    <form class="login-card" @submit.prevent="signIn">
      <div class="brand-mark">吉隆</div>
      <p class="eyebrow">地质灾害监测救援部署系统</p>
      <h1>救援组任务端</h1>
      <p class="hint">请使用后台登记的组长手机号登录</p>
      <label>
        <span>组长手机号</span>
        <input
          v-model.trim="phone"
          type="tel"
          inputmode="tel"
          autocomplete="username"
          placeholder="请输入手机号"
          required
        />
      </label>
      <label>
        <span>密码</span>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="默认密码 123"
          required
        />
      </label>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="busy">
        {{ busy ? "登录中…" : "登录" }}
      </button>
    </form>
  </main>

  <main v-else class="portal-page">
    <header class="portal-header">
      <div>
        <p>吉隆口岸救援组任务端</p>
        <strong>{{ team.name }}</strong>
      </div>
      <button type="button" class="text-button" @click="signOut">退出</button>
    </header>

    <div v-if="notice" class="notice" role="status">{{ notice }}</div>
    <div v-if="error" class="error-banner" role="alert" @click="error = ''">
      {{ error }} <span>×</span>
    </div>

    <section class="task-card">
      <div class="card-title">
        <div>
          <p class="eyebrow">救援组详情</p>
          <h1>当前任务</h1>
        </div>
        <span :class="['status-pill', selectedTask ? 'working' : 'waiting']">
          {{ selectedTask ? selectedTask.status : "未分配" }}
        </span>
      </div>

      <div v-if="!selectedTask" class="empty-state">
        <div class="empty-icon">✓</div>
        <h2>当前没有待执行任务</h2>
        <p>管理员分配新点位后，本页面会在 10 秒内自动更新。</p>
      </div>

      <form v-else class="task-form" @submit.prevent="submitReport(true)">
        <label v-if="activeTasks.length > 1" class="full-row">
          <span>选择当前任务</span>
          <select v-model="selectedTaskId">
            <option v-for="task in activeTasks" :key="task.id" :value="task.id">
              {{ task.task_number }}
            </option>
          </select>
        </label>
        <label>
          <span>任务编号</span>
          <input :value="selectedTask.task_number" readonly />
        </label>
        <label>
          <span>组名</span>
          <input :value="selectedTask.group" readonly />
        </label>
        <label>
          <span>当前阶段</span>
          <input :value="selectedTask.stage_label" readonly />
        </label>
        <label>
          <span>任务进度</span>
          <input :value="`${selectedTask.progress}%`" readonly />
        </label>

        <div class="progress full-row" aria-label="任务进度">
          <span :style="{ width: `${selectedTask.progress}%` }"></span>
        </div>

        <label class="upload-field full-row">
          <span>现场图片上传</span>
          <input
            ref="photoInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            @change="choosePhoto"
          />
          <small>支持 JPEG、PNG、WebP，单张不超过 10 MB</small>
        </label>

        <figure v-if="latestPhoto" class="latest-photo full-row">
          <figcaption>最近一次现场上报</figcaption>
          <img :src="latestPhoto.photo_url" alt="最近一次现场上报图片" />
        </figure>

        <div class="action-row full-row">
          <button
            type="button"
            class="secondary-button"
            :disabled="busy || !photo"
            @click="submitReport(false)"
          >
            仅上传图片
          </button>
          <button type="submit" class="primary-button" :disabled="busy">
            {{ busy ? "正在提交…" : advanceButtonText }}
          </button>
        </div>
      </form>
    </section>

    <section v-if="completedTasks.length" class="history-card">
      <h2>最近完成任务</h2>
      <div v-for="task in completedTasks" :key="task.id" class="history-row">
        <span>{{ task.task_number }}</span>
        <strong>已完成</strong>
      </div>
    </section>
  </main>
</template>
