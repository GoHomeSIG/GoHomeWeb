import axios from 'axios'

// 从环境变量读取 API 基础 URL（生产环境使用）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器 - 统一处理响应格式
api.interceptors.response.use(
  response => {
    // 如果响应包含 success 字段且为 false，抛出错误
    if (response.data && response.data.success === false) {
      return Promise.reject(new Error(response.data.message || '操作失败'))
    }
    return response
  },
  error => {
    if (error.response?.status === 401) {
      // 未授权，清除本地状态
      localStorage.removeItem('user')
      // 如果当前不在登录页，跳转到登录页
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

// API 方法
export const authAPI = {
  login: (username, password) => api.post('/login', { username, password }),
  register: (data) => api.post('/register', data),
  logout: () => api.get('/logout'),
  getCurrentUser: () => api.get('/me')
}

export const dashboardAPI = {
  getDashboard: () => api.get('/api/dashboard'),
  getProfile: () => api.get('/api/profile'),
  updateProfile: (data) => api.put('/api/profile', data)
}

export const profileAPI = {
  get: () => api.get('/api/profile'),
  update: (data) => api.put('/api/profile', data)
}

export const checkinAPI = {
  doCheckin: () => api.post('/api/checkin'),
  getStatus: () => api.get('/api/checkin/status'),
  getHistory: () => api.get('/api/checkin/history')
}

export const badgesAPI = {
  getList: () => api.get('/api/badges'),
  getDefinitions: () => api.get('/api/badges/definitions')
}

export const quotesAPI = {
  getList: () => api.get('/api/quotes'),
  add: (content, category) => api.post('/api/quotes', { content, category }),
  delete: (id) => api.delete(`/api/quotes/${id}`),
  getCategories: () => api.get('/api/quotes/categories')
}

export const aiQuoteAPI = {
  generate: (location, category) => api.post('/api/ai-quote/generate', { location, category }),
  generateBatch: (location) => api.post('/api/ai-quote/generate-batch', { location }),
  save: (content, category) => api.post('/api/ai-quote/save', { content, category }),
  getHistory: () => api.get('/api/ai-quote/history'),
  getCategories: () => api.get('/api/ai-quote/categories')
}
