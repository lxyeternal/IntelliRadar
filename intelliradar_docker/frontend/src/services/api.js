/**
 * IntelliRadar API Services
 */

import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============= Authentication APIs =============

export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getProfile: () => api.get('/auth/me'),
  logout: () => {
    localStorage.removeItem('access_token')
    return Promise.resolve()
  }
}

// ============= Threat Intelligence APIs =============

export const threatAPI = {
  // Get threat list
  getThreats: (params = {}) => {
    const {
      page = 1,
      page_size = 20,
      sort_by = 'metadata.last_updated',
      sort_order = 'desc',
      package_manager,
      confidence_level
    } = params

    const queryParams = new URLSearchParams({
      page: page.toString(),
      page_size: page_size.toString(),
      sort_by,
      sort_order
    })

    if (package_manager) queryParams.append('package_manager', package_manager)
    if (confidence_level) queryParams.append('confidence_level', confidence_level)

    return api.get(`/threats?${queryParams}`)
  },

  // Get threat details
  getThreatDetail: (threatId) => api.get(`/threats/${threatId}`),

  // Search threats
  searchThreats: (searchQuery) => api.post('/threats/search', searchQuery),

  // Get statistics
  getStatistics: () => api.get('/statistics')
}

// ============= Convenience Methods =============

export const fetchStats = async () => {
  try {
    return await threatAPI.getStatistics()
  } catch (error) {
    console.error('Failed to get statistics:', error)
    throw error
  }
}

export const fetchThreats = async (params) => {
  try {
    return await threatAPI.getThreats(params)
  } catch (error) {
    console.error('Failed to get threat list:', error)
    throw error
  }
}

export const fetchThreatDetail = async (threatId) => {
  try {
    return await threatAPI.getThreatDetail(threatId)
  } catch (error) {
    console.error('Failed to get threat details:', error)
    throw error
  }
}

export const searchThreats = async (query) => {
  try {
    return await threatAPI.searchThreats(query)
  } catch (error) {
    console.error('Failed to search threats:', error)
    throw error
  }
}

export default api
