import React, { createContext, useContext, useEffect, useMemo, useState, useRef } from 'react'
import { message } from 'antd'
import {
  loginUser,
  registerUser,
  getCurrentUser,
  setAuthToken,
  clearAuthToken,
  refreshAuthToken,
} from '../services/api'

const AuthContext = createContext(null)

const STORAGE_KEY = 'intelliradar_auth_token'
const REFRESH_INTERVAL = 50 * 60 * 1000 // Refresh every 50 minutes (token expires in 60 minutes)

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const refreshTimerRef = useRef(null)

  const fetchCurrentUser = async (overrideToken) => {
    const activeToken = overrideToken || token
    if (!activeToken) {
      setUser(null)
      clearAuthToken()
      return null
    }

    try {
      setAuthToken(activeToken)
      const profile = await getCurrentUser()
      setUser(profile)
      return profile
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      setUser(null)
      clearAuthToken()
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
  }

  useEffect(() => {
    const initialise = async () => {
      if (token) {
        await fetchCurrentUser(token)
      } else {
        clearAuthToken()
        setUser(null)
      }
      setLoading(false)
    }
    initialise()
  }, [token])

  const handleLogin = async ({ email, password }) => {
    const response = await loginUser({ email, password })
    if (response?.access_token) {
      localStorage.setItem(STORAGE_KEY, response.access_token)
      setToken(response.access_token)
      await fetchCurrentUser(response.access_token)
      message.success('Login successful')
    }
    return response
  }

  const handleRegister = async ({ email, password, fullName }) => {
    await registerUser({ email, password, fullName })
    message.success('Registration successful. You can now log in.')
  }

  const handleLogout = () => {
    // Clear refresh timer
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current)
      refreshTimerRef.current = null
    }
    
    clearAuthToken()
    localStorage.removeItem(STORAGE_KEY)
    setToken(null)
    setUser(null)
    message.success('Logged out successfully')
  }

  const handleTokenRefresh = async () => {
    try {
      const response = await refreshAuthToken()
      if (response?.access_token) {
        localStorage.setItem(STORAGE_KEY, response.access_token)
        setToken(response.access_token)
        setAuthToken(response.access_token)
        console.log('Token refreshed successfully')
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      // If refresh fails, logout the user
      handleLogout()
    }
  }

  // Setup auto-refresh timer when user is authenticated
  useEffect(() => {
    if (token && user) {
      // Clear any existing timer
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current)
      }
      
      // Set up new refresh timer (refresh every 50 minutes)
      refreshTimerRef.current = setInterval(() => {
        console.log('Auto-refreshing token...')
        handleTokenRefresh()
      }, REFRESH_INTERVAL)
      
      // Cleanup on unmount or when dependencies change
      return () => {
        if (refreshTimerRef.current) {
          clearInterval(refreshTimerRef.current)
        }
      }
    } else {
      // Clear timer if user logs out
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current)
        refreshTimerRef.current = null
      }
    }
  }, [token, user])

  const value = useMemo(() => ({
    token,
    user,
    loading,
    isAuthenticated: Boolean(token && user),
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshUser: fetchCurrentUser,
  }), [token, user, loading])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

