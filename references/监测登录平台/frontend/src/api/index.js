import axios from 'axios'

// 统一走 /api 前缀，开发环境由 Vite 代理到 Django 后端
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
})

export function login(username, password) {
  return api.post('/login/', { username, password })
}

export function register(username, password, confirmPassword) {
  return api.post('/register/', {
    username,
    password,
    confirm_password: confirmPassword,
  })
}

export function logout() {
  return api.get('/logout/')
}

export function getCurrentUser() {
  return api.get('/user/')
}

export default api
