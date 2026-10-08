import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Welcome from '../views/Welcome.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: Login },
    { path: '/register', name: 'register', component: Register },
    { path: '/welcome', name: 'welcome', component: Welcome, meta: { requiresAuth: true } },
  ],
})

// 简易登录守卫：访问需要登录的页面但本地没有登录标识时，跳回登录页
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !sessionStorage.getItem('username')) {
    return { name: 'login' }
  }
})

export default router
