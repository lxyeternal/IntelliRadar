import React from 'react'
import { Layout, Menu, Button, Dropdown, Space } from 'antd'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { HomeOutlined, DatabaseOutlined, RocketOutlined, UserOutlined, LogoutOutlined, LoginOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext.jsx'

const { Header } = Layout

const Navigation = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()
  
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">Home</Link>,
    },
    {
      key: '/database',
      icon: <DatabaseOutlined />,
      label: <Link to="/database">IntelliRadar Database</Link>,
    },
    {
      key: '/pipeline-monitor',
      icon: <RocketOutlined />,
      label: <Link to="/pipeline-monitor">Pipeline Monitor</Link>,
    },
  ]

  return (
    <Header style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    }}>
      <Link to="/" style={{ 
        display: 'flex', 
        alignItems: 'center',
        fontSize: '20px',
        fontWeight: 'bold',
        background: 'linear-gradient(45deg, #667eea, #764ba2)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        textDecoration: 'none',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.target.style.transform = 'scale(1.05)';
      }}
      onMouseLeave={(e) => {
        e.target.style.transform = 'scale(1)';
      }}>
        🛡️ IntelliRadar
      </Link>
      
      <Menu
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={menuItems}
        style={{
          background: 'transparent',
          border: 'none',
          flex: 1,
          justifyContent: 'center',
          fontSize: '16px',
        }}
      />
      
      <div style={{ width: '220px', display: 'flex', justifyContent: 'flex-end' }}>
        {isAuthenticated ? (
          <Dropdown
            overlayStyle={{ minWidth: 220 }}
            menu={{
              items: [
                {
                  key: 'profile',
                  disabled: true,
                  label: (
                    <div style={{ padding: '4px 4px' }}>
                      <div style={{ fontWeight: 600 }}>{user?.full_name || 'Signed in user'}</div>
                      <div style={{ fontSize: 12, color: '#8c8c8c' }}>{user?.email}</div>
                    </div>
                  ),
                },
                { type: 'divider' },
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: 'Log out',
                },
              ],
              onClick: ({ key }) => {
                if (key === 'logout') {
                  logout()
                  navigate('/')
                }
              },
            }}
            placement="bottomRight"
          >
            <Button 
              type="text" 
              icon={<UserOutlined />}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                maxWidth: '200px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                display: 'inline-flex',
                alignItems: 'center',
              }}
            >
              <span style={{ 
                overflow: 'hidden', 
                textOverflow: 'ellipsis', 
                whiteSpace: 'nowrap',
                maxWidth: '150px',
                display: 'inline-block'
              }}>
                {user?.email || 'Account'}
              </span>
            </Button>
          </Dropdown>
        ) : (
          <Space>
            <Button type="primary" ghost icon={<LoginOutlined />} onClick={() => navigate('/login')}>
              Sign in
            </Button>
            <Button type="primary" onClick={() => navigate('/register')}>
              Register
            </Button>
          </Space>
        )}
      </div>
    </Header>
  )
}

export default Navigation
