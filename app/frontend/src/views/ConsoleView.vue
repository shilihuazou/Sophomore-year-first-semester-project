<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  activeGroup: { type: String, default: "" },
  activeTeam: { type: String, default: "" },
  categories: { type: Array, required: true },
  rescueTeams: { type: Array, required: true },
  busy: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits([
  "back",
  "select-team",
  "clear-team-error",
  "create-team",
  "update-team",
  "delete-team",
]);

const expandedCategories = ref(
  new Set(props.activeGroup ? [props.activeGroup] : [props.categories[0]]),
);
const editorMode = ref("empty");
const confirmDeleteId = ref(null);
const form = ref(emptyForm(props.activeGroup || props.categories[0]));

const selectedTeam = computed(() =>
  props.rescueTeams.find((team) => team.name === props.activeTeam),
);
const draftTeam = computed(() =>
  editorMode.value === "create"
    ? {
        id: "draft",
        category: form.value.category,
        name: form.value.name || "新建队伍",
        status: "未保存",
        created_at: null,
        draft: true,
      }
    : null,
);

watch(
  () => props.activeGroup,
  (category) => {
    if (!category) return;
    expandedCategories.value = new Set([...expandedCategories.value, category]);
  },
  { immediate: true },
);

watch(
  [() => props.activeTeam, () => props.rescueTeams],
  () => {
    if (editorMode.value === "create") {
      if (selectedTeam.value?.name === form.value.name) {
        editorMode.value = "edit";
        form.value = teamForm(selectedTeam.value);
      }
      return;
    }
    if (!selectedTeam.value) {
      editorMode.value = "empty";
      return;
    }
    editorMode.value = "edit";
    form.value = teamForm(selectedTeam.value);
  },
  { immediate: true, deep: true },
);

function emptyForm(category) {
  return {
    category,
    name: "",
    captain: "",
    captain_phone: "",
    members: "",
    member_contacts: "",
    note: "",
  };
}

function teamForm(team) {
  return {
    category: team.category,
    name: team.name,
    captain: team.captain,
    captain_phone: team.captain_phone,
    members: team.members,
    member_contacts: team.member_contacts,
    note: team.note,
  };
}

function teamsFor(category) {
  return props.rescueTeams.filter((team) => team.category === category);
}

function displayTeamsFor(category) {
  const teams = teamsFor(category);
  return draftTeam.value?.category === category
    ? [...teams, draftTeam.value]
    : teams;
}

function suggestedName(category) {
  const names = new Set(props.rescueTeams.map((team) => team.name));
  let sequence = teamsFor(category).length + 1;
  let candidate = `${category}${String(sequence).padStart(2, "0")}`;
  while (names.has(candidate)) {
    sequence += 1;
    candidate = `${category}${String(sequence).padStart(2, "0")}`;
  }
  return candidate;
}

function toggleCategory(category) {
  const next = new Set(expandedCategories.value);
  if (next.has(category)) next.delete(category);
  else next.add(category);
  expandedCategories.value = next;
}

function startCreate(category) {
  expandedCategories.value = new Set([...expandedCategories.value, category]);
  editorMode.value = "create";
  form.value = emptyForm(category);
  form.value.name = suggestedName(category);
  confirmDeleteId.value = null;
  emit("clear-team-error");
}

function viewTeam(team) {
  if (team.draft) return;
  editorMode.value = "edit";
  form.value = teamForm(team);
  emit("select-team", team);
  emit("clear-team-error");
}

function closeEditor() {
  editorMode.value = "empty";
  form.value = emptyForm(props.activeGroup || props.categories[0]);
  confirmDeleteId.value = null;
  emit("clear-team-error");
}

function submit() {
  if (editorMode.value === "create") {
    emit("create-team", { ...form.value });
    return;
  }
  if (selectedTeam.value) {
    emit("update-team", {
      id: selectedTeam.value.id,
      values: { ...form.value },
    });
  }
}

function requestDelete(team) {
  if (confirmDeleteId.value !== team.id) {
    confirmDeleteId.value = team.id;
    return;
  }
  confirmDeleteId.value = null;
  emit("delete-team", team);
}

function formatTime(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}
</script>

<template>
  <section class="console-page rescue-admin-page">
    <button class="console-back" @click="emit('back')">返回</button>

    <div class="rescue-admin-grid">
      <section class="console-panel rescue-directory-panel">
        <div class="rescue-panel-heading">
          <h1>救援组管理</h1>
          <span>共 {{ rescueTeams.length + (draftTeam ? 1 : 0) }} 支队伍</span>
        </div>

        <div class="rescue-table-wrap">
          <table class="rescue-team-table">
            <thead>
              <tr>
                <th>组别</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="category in categories" :key="category">
                <tr class="rescue-category-row">
                  <td>
                    <button
                      class="category-toggle"
                      :aria-expanded="expandedCategories.has(category)"
                      @click="toggleCategory(category)"
                    >
                      <span>{{
                        expandedCategories.has(category) ? "⌄" : "›"
                      }}</span>
                      {{ category }}
                    </button>
                  </td>
                  <td>—</td>
                  <td>—</td>
                  <td>
                    <button
                      class="outline-create-button"
                      @click="startCreate(category)"
                    >
                      新增
                    </button>
                  </td>
                </tr>
                <tr
                  v-for="team in expandedCategories.has(category)
                    ? displayTeamsFor(category)
                    : []"
                  :key="team.id"
                  class="rescue-team-row"
                  :class="{
                    selected: team.draft || activeTeam === team.name,
                    draft: team.draft,
                  }"
                >
                  <td><span class="tree-branch">└</span>{{ team.name }}</td>
                  <td>
                    <span class="team-status" :class="`status-${team.status}`">
                      <i></i>{{ team.status }}
                    </span>
                  </td>
                  <td>
                    {{ team.created_at ? formatTime(team.created_at) : "—" }}
                  </td>
                  <td class="row-actions">
                    <template v-if="team.draft">
                      <button class="cancel-delete" @click="closeEditor">
                        取消
                      </button>
                      <span></span>
                      <button @click="editorMode = 'create'">编辑</button>
                    </template>
                    <template v-else>
                      <button
                        v-if="confirmDeleteId === team.id"
                        class="cancel-delete"
                        @click="confirmDeleteId = null"
                      >
                        取消
                      </button>
                      <button :disabled="busy" @click="requestDelete(team)">
                        {{ confirmDeleteId === team.id ? "确认删除" : "删除" }}
                      </button>
                      <span></span>
                      <button @click="viewTeam(team)">查看</button>
                    </template>
                  </td>
                </tr>
                <tr
                  v-if="
                    expandedCategories.has(category) &&
                    !displayTeamsFor(category).length
                  "
                  class="empty-category-row"
                >
                  <td colspan="4">该类别尚未新增队伍</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>

      <section class="console-panel rescue-editor-panel">
        <div class="rescue-editor-heading">
          <h2>救援组详情</h2>
          <button
            type="button"
            aria-label="关闭救援组详情"
            @click="closeEditor"
          >
            ×
          </button>
        </div>

        <div v-if="editorMode === 'empty'" class="rescue-editor-empty">
          请选择左侧队伍查看详情，或在类别行点击“新增”。
        </div>

        <form v-else class="rescue-team-form" @submit.prevent="submit">
          <label>
            <span>所属类别</span>
            <select v-model="form.category" required>
              <option
                v-for="category in categories"
                :key="category"
                :value="category"
              >
                {{ category }}
              </option>
            </select>
          </label>
          <label>
            <span>组名</span>
            <input v-model.trim="form.name" maxlength="80" required />
          </label>
          <label>
            <span>组长</span>
            <input
              v-model.trim="form.captain"
              maxlength="80"
              placeholder="待录入"
            />
          </label>
          <label>
            <span>组长联系方式</span>
            <input
              v-model.trim="form.captain_phone"
              maxlength="80"
              placeholder="待录入"
            />
          </label>
          <label>
            <span>各组员</span>
            <textarea
              v-model="form.members"
              maxlength="2000"
              rows="3"
            ></textarea>
          </label>
          <label>
            <span>各组员联系方式</span>
            <textarea
              v-model="form.member_contacts"
              maxlength="2000"
              rows="3"
            ></textarea>
          </label>
          <label>
            <span>组备注</span>
            <textarea v-model="form.note" maxlength="2000" rows="3"></textarea>
          </label>

          <p v-if="error" class="rescue-form-error" role="alert">{{ error }}</p>
          <div class="rescue-form-actions">
            <button
              type="button"
              class="ghost-btn"
              :disabled="busy"
              @click="closeEditor"
            >
              关闭
            </button>
            <button type="submit" class="primary-btn" :disabled="busy">
              {{ busy ? "保存中…" : "保存" }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </section>
</template>
