import React, { useState } from 'react'
import { Card, Tabs, Form, Input, Button, Typography, Alert, message } from 'antd'
import { LockOutlined, MailOutlined, UserOutlined, LoginOutlined, UserAddOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import './Auth.css'

const { Title, Text } = Typography

const AuthPage = () => {
  const { login, register, isAuthenticated, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [activeKey, setActiveKey] = useState('login')
  const [submitting, setSubmitting] = useState(false)
  const redirectPath = location.state?.from || '/database'

  const handleLogin = async (values) => {
    setSubmitting(true)
    try {
      await login({ email: values.email.trim().toLowerCase(), password: values.password })
      navigate(redirectPath, { replace: true })
    } catch (error) {
      const detail = error?.body ? (() => {
        try {
          const parsed = JSON.parse(error.body)
          return parsed?.detail || error.message
        } catch (_) {
          return error.message
        }
      })() : error?.message
      message.error(detail || 'Unable to sign in')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRegister = async (values) => {
    setSubmitting(true)
    try {
      await register({
        email: values.email.trim().toLowerCase(),
        password: values.password,
        fullName: values.fullName || '',
      })
      setActiveKey('login')
    } catch (error) {
      const detail = error?.body ? (() => {
        try {
          const parsed = JSON.parse(error.body)
          return parsed?.detail || error.message
        } catch (_) {
          return error.message
        }
      })() : error?.message
      message.error(detail || 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-hero">
        <Title level={2} className="auth-title">Secure Access</Title>
        <Text className="auth-subtitle">
          Sign in to unlock full ChainGuard intelligence, or create an account in seconds.
        </Text>
      </div>

      <Card className="auth-card" bordered={false}>
        {isAuthenticated && user ? (
          <Alert
            type="success"
            message="You are already signed in."
            description="Use the navigation bar to explore the database or pipeline monitor."
            showIcon
            style={{ marginBottom: 24 }}
          />
        ) : null}

        <Tabs
          activeKey={activeKey}
          onChange={setActiveKey}
          centered
          items={[
            {
              key: 'login',
              label: (
                <span>
                  <LoginOutlined /> Log In
                </span>
              ),
              children: (
                <Form layout="vertical" onFinish={handleLogin}>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Email is required' },
                      { type: 'email', message: 'Enter a valid email address' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} placeholder="you@example.com" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    label="Password"
                    rules={[{ required: true, message: 'Password is required' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="Enter your password" size="large" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
                      Sign In
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: (
                <span>
                  <UserAddOutlined /> Register
                </span>
              ),
              children: (
                <Form layout="vertical" onFinish={handleRegister}>
                  <Form.Item
                    name="fullName"
                    label="Full Name"
                  >
                    <Input prefix={<UserOutlined />} placeholder="Optional" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Email is required' },
                      { type: 'email', message: 'Enter a valid email address' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} placeholder="you@example.com" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    label="Password"
                    rules={[
                      { required: true, message: 'Password is required' },
                      { min: 6, message: 'Password must be at least 6 characters long' },
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="Create a password" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="confirm"
                    label="Confirm Password"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: 'Please confirm your password' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve()
                          }
                          return Promise.reject(new Error('Passwords do not match'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="Repeat your password" size="large" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
                      Create Account
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default AuthPage
