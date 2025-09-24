import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import { ConfigProvider, Layout, Menu, Typography, Space, Button } from 'antd'
import {
  DatabaseOutlined,
  SearchOutlined,
  BarChartOutlined,
  HomeOutlined,
  BugOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'

// Import pages
import HomePage from './pages/HomePage'
import ThreatDatabase from './pages/ThreatDatabase'
import Search from './pages/Search'
import Statistics from './pages/Statistics'
import ThreatDetail from './pages/ThreatDetail'

import './App.css'

const { Header, Content, Footer, Sider } = Layout
const { Title, Text } = Typography

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Menu items
const menuItems = [
  {
    key: '/',
    icon: <HomeOutlined />,
    label: 'Home',
  },
  {
    key: '/threats',
    icon: <DatabaseOutlined />,
    label: 'Threat Database',
  },
  {
    key: '/search',
    icon: <SearchOutlined />,
    label: 'Advanced Search',
  },
  {
    key: '/statistics',
    icon: <BarChartOutlined />,
    label: 'Statistics',
  },
]

function App() {
  const [collapsed, setCollapsed] = React.useState(false)
  const [selectedKeys, setSelectedKeys] = React.useState(['/'])

  const handleMenuClick = ({ key }) => {
    setSelectedKeys([key])
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <Router>
          <Layout style={{ minHeight: '100vh' }}>
            {/* Sidebar */}
            <Sider
              collapsible
              collapsed={collapsed}
              onCollapse={setCollapsed}
              theme="dark"
              width={250}
            >
              <motion.div
                className="logo"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{
                  height: 64,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: collapsed ? 16 : 20,
                  fontWeight: 'bold',
                  padding: '0 16px',
                }}
              >
                <BugOutlined style={{ marginRight: collapsed ? 0 : 8 }} />
                {!collapsed && 'IntelliRadar'}
              </motion.div>

              <Menu
                theme="dark"
                selectedKeys={selectedKeys}
                mode="inline"
                items={menuItems}
                onClick={handleMenuClick}
                style={{ borderRight: 0 }}
              />
            </Sider>

            <Layout>
              {/* Header */}
              <Header
                style={{
                  background: '#fff',
                  padding: '0 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                }}
              >
                <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                  Malicious Package Manager Component Threat Intelligence Database
                </Title>
                
                <Space>
                  <Button type="primary" ghost>
                    API Documentation
                  </Button>
                  <Button>
                    About
                  </Button>
                </Space>
              </Header>

              {/* Main Content */}
              <Content style={{ margin: '24px', minHeight: 'calc(100vh - 134px)' }}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/threats" element={<ThreatDatabase />} />
                  <Route path="/threats/:threatId" element={<ThreatDetail />} />
                  <Route path="/search" element={<Search />} />
                  <Route path="/statistics" element={<Statistics />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Content>

              {/* Footer */}
              <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
                <Text type="secondary">
                  IntelliRadar ©2024 - Malicious Package Intelligence Platform
                </Text>
              </Footer>
            </Layout>
          </Layout>
        </Router>
      </ConfigProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

export default App
