<template>
  <div class="register-page">
    <!-- ======== 轮播背景层（与登录页一致） ======== -->
    <div class="bg-slideshow">
      <div
        v-for="(photo, i) in photos"
        :key="i"
        class="bg-slide"
        :class="{ active: i === currentIndex }"
        :style="{ backgroundImage: `url(${photo.src})` }"
      ></div>
      <div class="bg-overlay"></div>
    </div>

    <!-- ======== 注册卡片 ======== -->
    <div class="register-card">
      <h1 class="register-title">注册账号</h1>
      <p class="register-subtitle">创建账号，加入洪水监测平台</p>

      <form class="register-form" @submit.prevent="handleRegister">
        <label class="field">
          <span class="field-label">用户名</span>
          <input
            v-model.trim="username"
            type="text"
            placeholder="至少 3 个字符"
            autocomplete="username"
            required
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="至少 6 位"
            autocomplete="new-password"
            required
          />
        </label>

        <label class="field">
          <span class="field-label">确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
            required
          />
        </label>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? '注册中…' : '注 册' }}
        </button>
      </form>

      <p class="login-link">
        已有账号？
        <a href="javascript:void(0)" @click="goLogin">返回登录</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { backgroundPhotos as photos } from '../assets/bg-config'
import { register } from '../api'

const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const loading = ref(false)

const currentIndex = ref(0)
let timer = null
const INTERVAL = 6000 // 背景同样每 6 秒自动切换

function next() {
  currentIndex.value = (currentIndex.value + 1) % photos.length
}

onMounted(() => {
  timer = setInterval(next, INTERVAL)
})
onBeforeUnmount(() => clearInterval(timer))

async function handleRegister() {
  if (!username.value || !password.value || !confirmPassword.value) {
    errorMsg.value = '请填写完整的注册信息'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await register(username.value, password.value, confirmPassword.value)
    if (res.data.code === 0) {
      // 注册成功，回登录页并提示
      router.push({ path: '/login', query: { registered: 1 } })
    } else {
      errorMsg.value = res.data.msg || '注册失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误，请确认后端服务已启动（127.0.0.1:8000）'
  } finally {
    loading.value = false
  }
}

function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
/* ---------- 页面与背景 ---------- */
.register-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-slideshow {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-slide {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  opacity: 0;
  transition: opacity 1.4s ease;
}

.bg-slide.active {
  opacity: 1;
  animation: kenburns 8s ease-out forwards;
}

@keyframes kenburns {
  from { transform: scale(1); }
  to   { transform: scale(1.1); }
}

.bg-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(160deg, rgba(10, 14, 32, 0.55), rgba(10, 14, 32, 0.35) 50%, rgba(10, 14, 32, 0.65));
}

/* ---------- 注册卡片 ---------- */
.register-card {
  position: relative;
  z-index: 10;
  width: 380px;
  max-width: calc(100vw - 48px);
  padding: 36px 36px 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(18px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.35);
  color: #fff;
}

.register-title {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 2px;
}

.register-subtitle {
  margin: 0 0 24px;
  font-size: 13px;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
}

.field { display: block; margin-bottom: 16px; }
.field-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}
.field input {
  box-sizing: border-box;
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}
.field input::placeholder { color: rgba(255, 255, 255, 0.45); }
.field input:focus {
  border-color: #5aa7ff;
  background: rgba(255, 255, 255, 0.18);
}

.error-msg {
  margin: -2px 0 14px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255, 77, 79, 0.22);
  border: 1px solid rgba(255, 77, 79, 0.45);
  font-size: 13px;
  color: #ffd6d6;
}

.submit-btn {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(90deg, #2f6bff, #5aa7ff);
  color: #fff;
  font-size: 15px;
  letter-spacing: 6px;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}
.submit-btn:hover:not(:disabled) { opacity: 0.9; }
.submit-btn:active:not(:disabled) { transform: scale(0.98); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.login-link {
  margin: 16px 0 0;
  font-size: 13px;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
}
.login-link a {
  color: #7fb2ff;
  text-decoration: none;
}
.login-link a:hover { text-decoration: underline; }
</style>
