import axios from 'axios'

// 在开发环境直接请求后端，避免与前端路由冲突
const api = axios.create({
  baseURL: 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  // 附加JWT到管理端接口
  if (config.url && config.url.startsWith('/admin')) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers = config.headers || {}
      config.headers['Authorization'] = `Bearer ${token}`
    }
  }
  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err?.response?.status === 401) {
      // 未授权跳转登录
      if (location.pathname.startsWith('/admin')) {
        location.href = '/admin/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api