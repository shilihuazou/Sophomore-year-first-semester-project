<template>
  <div class="welcome-page">
    <header class="topbar">
      <span class="logo">登录平台</span>
      <div class="user-area">
        <span class="username">👤 {{ username }}</span>
        <button class="logout-btn" type="button" @click="handleLogout">退出登录</button>
      </div>
    </header>

    <main class="welcome-body">
      <div class="welcome-card">
        <h1>欢迎回来，{{ username }}</h1>
        <p>登录成功！你现在已经进入了登录平台。</p>
        <p class="hint">这里可以继续开发你的业务页面（仪表盘、数据大屏等）。</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, logout } from '../api'

const router = useRouter()
const username = ref(sessionStorage.getItem('username') || '')

// 页面加载时向后端校验会话是否仍然有效
onMounted(async () => {
  try {
    const res = await getCurrentUser()
    if (res.data.code === 0) {
      username.value = res.data.data.username
      sessionStorage.setItem('username', username.value)
    } else {
      // 会话已失效，回登录页
      sessionStorage.removeItem('username')
      router.replace('/login')
    }
  } catch (e) {
    // 后端不可用时先不打扰用户，仅保留本地登录态
  }
})

async function handleLogout() {
  try {
    await logout()
  } catch (e) {
    // 忽略网络错误，本地照常退出
  }
  sessionStorage.removeItem('username')
  router.replace('/login')
}
</script>

<style scoped>
.welcome-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg, #0b1030, #1c2756 55%, #0b1030);
  color: #fff;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
}
.logo { font-size: 18px; font-weight: 700; letter-spacing: 2px; }
.user-area { display: flex; align-items: center; gap: 14px; }
.username { font-size: 14px; opacity: 0.9; }
.logout-btn {
  padding: 6px 14px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 6px;
  background: transparent;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}
.logout-btn:hover { background: rgba(255, 255, 255, 0.15); }

.welcome-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome-card {
  max-width: 520px;
  padding: 48px 40px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  text-align: center;
}
.welcome-card h1 { margin: 0 0 14px; font-size: 24px; }
.welcome-card p { margin: 8px 0; font-size: 14px; opacity: 0.85; }
.hint { opacity: 0.6 !important; font-size: 13px !important; }
</style>
