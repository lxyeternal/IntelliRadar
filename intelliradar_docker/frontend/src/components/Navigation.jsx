import React from 'react'
import { Layout, Menu } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { HomeOutlined, DatabaseOutlined } from '@ant-design/icons'

const { Header } = Layout

const Navigation = () => {
  const location = useLocation()
  
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
      <div style={{ 
        display: 'flex', 
        alignItems: 'center',
        fontSize: '20px',
        fontWeight: 'bold',
        background: 'linear-gradient(45deg, #667eea, #764ba2)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }}>
        🛡️ IntelliRadar
      </div>
      
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
      
      <div style={{ width: '120px' }}></div>
    </Header>
  )
}

export default Navigation
