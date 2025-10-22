// API service for IntelliRadar

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api'
let authToken = null

export const setAuthToken = (token) => {
  authToken = token
}

export const clearAuthToken = () => {
  authToken = null
}

// Helper function to build query string
const buildQueryString = (params) => {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, value)
    }
  })
  
  return searchParams.toString()
}

// Generic API call function
const apiCall = async (endpoint, options = {}) => {
  let normalizedEndpoint = endpoint

  if (API_BASE_URL.endsWith('/api') && endpoint.startsWith('/api/')) {
    normalizedEndpoint = endpoint.substring(4)
  }

  const url = `${API_BASE_URL}${normalizedEndpoint}`
  
  try {
    console.log('API Call:', url, options)
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`
    }

    const response = await fetch(url, {
      headers: {
        ...headers,
      },
      ...options,
    })

    console.log('API Response Status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error Response:', errorText)
      const error = new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      error.status = response.status
      error.body = errorText
      throw error
    }

    const data = await response.json()
    console.log('API Response Data:', data)
    return data
  } catch (error) {
    console.error('API call failed:', error)
    throw error
  }
}

// Get threats list with filters and pagination
export const getThreats = async (params = {}) => {
  const queryString = buildQueryString(params)
  const endpoint = queryString ? `/api/threats?${queryString}` : '/api/threats'
  return apiCall(endpoint)
}

// Get threat details by ID
export const getThreatDetail = async (threatId) => {
  if (!threatId) {
    throw new Error('Threat ID is required')
  }
  return apiCall(`/api/threats/${encodeURIComponent(threatId)}`)
}

// Search threats
export const searchThreats = async (searchQuery) => {
  return apiCall('/api/threats/search', {
    method: 'POST',
    body: JSON.stringify(searchQuery),
  })
}

// Get statistics
export const getStatistics = async () => {
  return apiCall('/api/statistics')
}

// Get latest threats for homepage
export const getLatestThreats = async () => {
  return apiCall('/api/threats/latest')
}

// Health check
export const healthCheck = async () => {
  return apiCall('/api/health')
}

export const registerUser = async ({ email, password, fullName }) => {
  return apiCall('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
    }),
  })
}

export const loginUser = async ({ email, password }) => {
  const body = new URLSearchParams()
  body.append('username', email)
  body.append('password', password)

  return apiCall('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  })
}

export const getCurrentUser = async () => {
  return apiCall('/api/auth/me')
}

export const refreshAuthToken = async () => {
  return apiCall('/api/auth/refresh', {
    method: 'POST',
  })
}

// Pipeline task monitor endpoints
export const getTaskDashboardSummary = async () => {
  return apiCall('/api/tasks/dashboard/summary')
}

export const getLatestPipelineTasks = async (limit = 10) => {
  const query = limit ? `?limit=${encodeURIComponent(limit)}` : ''
  return apiCall(`/api/tasks/latest${query}`)
}

export const getRunningPipelineTasks = async () => {
  return apiCall('/api/tasks/running/current')
}

export const getSourcePerformanceStats = async (days = 30) => {
  const query = days ? `?days=${encodeURIComponent(days)}` : ''
  return apiCall(`/api/tasks/statistics/sources${query}`)
}

export const getPipelineTaskDetail = async (taskId) => {
  if (!taskId) {
    throw new Error('Task ID is required')
  }
  return apiCall(`/api/tasks/${encodeURIComponent(taskId)}`)
}

export default {
  getThreats,
  getThreatDetail,
  searchThreats,
  getStatistics,
  getLatestThreats,
  healthCheck,
  getTaskDashboardSummary,
  getLatestPipelineTasks,
  getRunningPipelineTasks,
  getSourcePerformanceStats,
  getPipelineTaskDetail,
  registerUser,
  loginUser,
  getCurrentUser,
  setAuthToken,
  clearAuthToken,
}
