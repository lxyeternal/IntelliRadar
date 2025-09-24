// API service for IntelliRadar

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

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
  const url = `${API_BASE_URL}${endpoint}`
  
  try {
    console.log('API Call:', url, options)
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    console.log('API Response Status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error Response:', errorText)
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
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

export default {
  getThreats,
  getThreatDetail,
  searchThreats,
  getStatistics,
  getLatestThreats,
  healthCheck,
}