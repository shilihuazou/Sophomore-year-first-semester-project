<script setup>
import { ref } from "vue";

defineProps({
  busy: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["close", "submit"]);
const form = ref({
  current_password: "",
  new_password: "",
  confirm_password: "",
});
const clientError = ref("");

function submit() {
  clientError.value = "";
  if (form.value.new_password !== form.value.confirm_password) {
    clientError.value = "两次输入的新密码不一致";
    return;
  }
  emit("submit", { ...form.value });
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <section
      class="modal-card password-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-password-title"
    >
      <div class="modal-head">
        <div>
          <span class="section-number">ACCOUNT SECURITY</span>
          <h2 id="change-password-title">修改密码</h2>
        </div>
        <button
          type="button"
          aria-label="关闭修改密码窗口"
          @click="emit('close')"
        >
          ×
        </button>
      </div>

      <form class="password-form" @submit.prevent="submit">
        <label>
          <span>原密码</span>
          <input
            v-model="form.current_password"
            type="password"
            autocomplete="current-password"
            required
            autofocus
          />
        </label>
        <label>
          <span>新密码</span>
          <input
            v-model="form.new_password"
            type="password"
            autocomplete="new-password"
            required
          />
        </label>
        <label>
          <span>确认新密码</span>
          <input
            v-model="form.confirm_password"
            type="password"
            autocomplete="new-password"
            required
          />
        </label>

        <p class="modal-note">
          新密码至少 8 位，不能是纯数字，也不能与账号或常见密码过于相似。
        </p>
        <p v-if="clientError || error" class="password-error" role="alert">
          {{ clientError || error }}
        </p>
        <div class="modal-actions">
          <button
            type="button"
            class="ghost-btn"
            :disabled="busy"
            @click="emit('close')"
          >
            取消
          </button>
          <button type="submit" class="primary-btn" :disabled="busy">
            {{ busy ? "保存中…" : "确认修改" }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
