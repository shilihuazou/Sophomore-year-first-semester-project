<template>
  <div class="login-page">
    <!-- ======== 轮播背景层 ======== -->
    <div class="bg-slideshow">
      <div
        v-for="(photo, i) in photos"
        :key="i"
        class="bg-slide"
        :class="{ active: i === currentIndex }"
        :style="{ backgroundImage: `url(${photo.src})` }"
      ></div>
      <!-- 半透明遮罩，保证文字可读性 -->
      <div class="bg-overlay"></div>
    </div>

    <!-- ======== 登录卡片 ======== -->
    <div class="login-card">
      <h1 class="login-title">登录平台</h1>
      <p class="login-subtitle">欢迎回来，请登录你的账号</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <label class="field">
          <span class="field-label">用户名</span>
          <input
            v-model.trim="username"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            required
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            required
          />
        </label>

        <p v-if="errorMsg" class="error-msg" :class="{ 'success-msg': isRegistered }">{{ errorMsg }}</p>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <p class="register-link">
        还没有账号？
        <a href="javascript:void(0)" @click="goRegister">立即注册</a>
      </p>

      <p class="login-tip">测试账号：admin / 123456</p>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { backgroundPhotos as photos } from '../assets/bg-config'
import { login } from '../api'

const router = useRouter()
const route = useRoute()

const currentIndex = ref(0)
const username = ref('')
const password = ref('')
const errorMsg = ref(route.query.registered ? '注册成功，请登录' : '')
const isRegistered = ref(!!route.query.registered)
const loading = ref(false)

let timer = null
const INTERVAL = 6000 // 每 6 秒自动切换一张

function next() {
  currentIndex.value = (currentIndex.value + 1) % photos.length
}

function startAutoPlay() {
  timer = setInterval(next, INTERVAL)
}

function goRegister() {
  router.push('/register')
}

onMounted(startAutoPlay)
onBeforeUnmount(() => clearInterval(timer))

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await login(username.value, password.value)
    if (res.data.code === 0) {
      sessionStorage.setItem('username', res.data.data.username)
      router.push('/welcome')
    } else {
      errorMsg.value = res.data.msg || '登录失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误，请确认后端服务已启动（127.0.0.1:8000）'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ---------- 页面与背景 ---------- */
.login-page {
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

/* 当前播放的照片淡入，并做缓慢放大（Ken Burns 效果） */
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

/* ---------- 登录卡片 ---------- */
.login-card {
  position: relative;
  z-index: 10;
  width: 380px;
  max-width: calc(100vw - 48px);
  padding: 40px 36px 30px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(18px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.35);
  color: #fff;
}

.login-title {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 2px;
}

.login-subtitle {
  margin: 0 0 26px;
  font-size: 13px;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
}

.field { display: block; margin-bottom: 18px; }
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
  margin: -4px 0 14px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255, 77, 79, 0.22);
  border: 1px solid rgba(255, 77, 79, 0.45);
  font-size: 13px;
  color: #ffd6d6;
}

.success-msg {
  background: rgba(82, 196, 26, 0.22);
  border-color: rgba(82, 196, 26, 0.5);
  color: #d9f7be;
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

.login-tip {
  margin: 18px 0 0;
  font-size: 12px;
  text-align: center;
  color: rgba(255, 255, 255, 0.55);
}

.register-link {
  margin: 16px 0 0;
  font-size: 13px;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
}
.register-link a {
  color: #7fb2ff;
  text-decoration: none;
}
.register-link a:hover { text-decoration: underline; }
</style>
