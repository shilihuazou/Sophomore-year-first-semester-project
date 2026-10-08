<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import debrisFlowBackground from "../assets/login/geohazards/01-debris-flow.jpg";
import landslideBackground from "../assets/login/geohazards/02-landslide.jpg";
import rockfallBackground from "../assets/login/geohazards/03-rockfall.jpg";
import earthquakeScarpBackground from "../assets/login/geohazards/04-earthquake-scarp.jpg";
import volcanicEruptionBackground from "../assets/login/geohazards/05-volcanic-eruption.jpg";
import avalancheBackground from "../assets/login/geohazards/06-avalanche.jpg";
import sinkholeBackground from "../assets/login/geohazards/07-sinkhole.jpg";

defineProps({
  busy: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["submit"]);
const backgrounds = [
  debrisFlowBackground,
  landslideBackground,
  rockfallBackground,
  earthquakeScarpBackground,
  volcanicEruptionBackground,
  avalancheBackground,
  sinkholeBackground,
];
const activeBackground = ref(0);
const form = ref({ username: "", password: "" });
let backgroundTimer;

onMounted(() => {
  backgroundTimer = window.setInterval(() => {
    activeBackground.value = (activeBackground.value + 1) % backgrounds.length;
  }, 6000);
});

onUnmounted(() => window.clearInterval(backgroundTimer));

function submit() {
  emit("submit", { ...form.value });
  form.value.password = "";
}
</script>

<template>
  <main class="monitor-login-page">
    <div class="monitor-login-slideshow" aria-hidden="true">
      <div
        v-for="(background, index) in backgrounds"
        :key="background"
        class="monitor-login-slide"
        :class="{ active: index === activeBackground }"
        :style="{ backgroundImage: `url(${background})` }"
      ></div>
      <div class="monitor-login-overlay"></div>
    </div>
    <section class="monitor-login-card" aria-labelledby="monitor-login-title">
      <div class="monitor-login-brand"><span>KQ</span>GIS</div>
      <h1 id="monitor-login-title">地质灾害监测救援部署系统</h1>
      <p class="monitor-login-subtitle">以吉隆口岸泥石流灾害为例</p>
      <form class="monitor-login-form" @submit.prevent="submit">
        <label class="monitor-login-field">
          <span>用户名</span>
          <input
            v-model.trim="form.username"
            type="text"
            autocomplete="username"
            placeholder="请输入管理员账号"
            required
          />
        </label>
        <label class="monitor-login-field">
          <span>密码</span>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            required
          />
        </label>
        <p v-if="error" class="monitor-login-error" role="alert">{{ error }}</p>
        <button class="monitor-login-submit" type="submit" :disabled="busy">
          {{ busy ? "登录中…" : "登 录" }}
        </button>
      </form>
      <p class="monitor-login-tip">管理员账号：admin / 123</p>
    </section>
  </main>
</template>
