import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Typography,
  Space,
  Alert,
  Spin,
  Progress,
  Tag,
  List,
  Avatar,
  Badge
} from 'antd'
import {
  DatabaseOutlined,
  SearchOutlined,
  BarChartOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BugOutlined,
  SecurityScanOutlined,
  GlobalOutlined,
  RocketOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import { fetchStats } from '../services/api'
import './HomePage.css'

const { Title, Paragraph, Text } = Typography

const HomePage = () => {
  const navigate = useNavigate()

  // Fetch statistics data
  const {
    data: stats,
    isLoading,
    error
  } = useQuery('homepage-stats', fetchStats, {
    refetchInterval: 300000, // Refresh every 5 minutes
  })

  // Feature cards data
  const features = [
    {
      icon: <DatabaseOutlined className="feature-icon" />,
      title: 'Threat Database',
      description: 'Comprehensive collection of malicious package threat intelligence data',
      color: '#1890ff',
      action: () => navigate('/threats')
    },
    {
      icon: <SearchOutlined className="feature-icon" />,
      title: 'Advanced Search',
      description: 'Multi-dimensional search for precise threat intelligence queries',
      color: '#52c41a',
      action: () => navigate('/search')
    },
    {
      icon: <BarChartOutlined className="feature-icon" />,
      title: 'Statistics Analysis',
      description: 'Real-time statistics and trend analysis of threat landscape',
      color: '#faad14',
      action: () => navigate('/statistics')
    }
  ]

  // Package manager statistics
  const packageManagers = [
    { name: 'NPM', color: '#cb3837', count: stats?.package_managers?.find(p => p._id === 'npm')?.count || 0 },
    { name: 'PyPI', color: '#3776ab', count: stats?.package_managers?.find(p => p._id === 'pypi')?.count || 0 },
    { name: 'Maven', color: '#f89820', count: stats?.package_managers?.find(p => p._id === 'maven')?.count || 0 },
    { name: 'NuGet', color: '#004880', count: stats?.package_managers?.find(p => p._id === 'nuget')?.count || 0 },
  ]

  if (error) {
    return (
      <div className="home-page">
        <Alert
          message="Failed to Load Data"
          description="Unable to retrieve homepage statistics. Please check your network connection or try again later."
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              Retry
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="home-page">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="hero-section"
      >
        <Card className="hero-card">
          <Row align="middle" gutter={[32, 24]}>
            <Col xs={24} lg={12}>
              <div className="hero-content">
                <Title level={1} className="hero-title">
                  <BugOutlined className="hero-icon" />
                  IntelliRadar
                </Title>
                <Title level={2} className="hero-subtitle">
                  Malicious Package Intelligence Platform
                </Title>
                <Paragraph className="hero-description">
                  A comprehensive threat intelligence database for malicious components 
                  across major package managers. Real-time monitoring, intelligent analysis, 
                  and proactive security protection for your software supply chain.
                </Paragraph>
                <Space size="large" className="hero-actions">
                  <Button
                    type="primary"
                    size="large"
                    icon={<SearchOutlined />}
                    onClick={() => navigate('/search')}
                    className="hero-btn"
                  >
                    Start Searching
                  </Button>
                  <Button
                    size="large"
                    icon={<DatabaseOutlined />}
                    onClick={() => navigate('/threats')}
                    className="hero-btn-secondary"
                  >
                    Browse Database
                  </Button>
                </Space>
              </div>
            </Col>
            <Col xs={24} lg={12}>
              <div className="hero-stats">
                <Row gutter={[16, 16]}>
                  <Col xs={12}>
                    <Card className="stat-card-mini">
                      <Statistic
                        title="Total Threats"
                        value={stats?.total_threats || 0}
                        prefix={<ExclamationCircleOutlined />}
                        valueStyle={{ color: '#ff4d4f', fontSize: '24px' }}
                      />
                    </Card>
                  </Col>
                  <Col xs={12}>
                    <Card className="stat-card-mini">
                      <Statistic
                        title="Package Managers"
                        value={stats?.package_managers?.length || 0}
                        prefix={<GlobalOutlined />}
                        valueStyle={{ color: '#1890ff', fontSize: '24px' }}
                      />
                    </Card>
                  </Col>
                  <Col xs={12}>
                    <Card className="stat-card-mini">
                      <Statistic
                        title="High Confidence"
                        value={stats?.confidence_distribution?.high || 0}
                        prefix={<SecurityScanOutlined />}
                        valueStyle={{ color: '#52c41a', fontSize: '24px' }}
                      />
                    </Card>
                  </Col>
                  <Col xs={12}>
                    <Card className="stat-card-mini">
                      <Statistic
                        title="Recent Updates"
                        value={stats?.recent_updates?.length || 0}
                        prefix={<ClockCircleOutlined />}
                        valueStyle={{ color: '#faad14', fontSize: '24px' }}
                      />
                    </Card>
                  </Col>
                </Row>
              </div>
            </Col>
          </Row>
        </Card>
      </motion.div>

      {/* Features Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="features-section"
      >
        <Title level={2} className="section-title">
          Core Features
        </Title>
        <Row gutter={[24, 24]}>
          {features.map((feature, index) => (
            <Col xs={24} md={8} key={index}>
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card
                  className="feature-card"
                  hoverable
                  onClick={feature.action}
                  bodyStyle={{ textAlign: 'center', padding: '32px 24px' }}
                >
                  <div
                    className="feature-icon-wrapper"
                    style={{ backgroundColor: `${feature.color}15` }}
                  >
                    {React.cloneElement(feature.icon, { style: { color: feature.color } })}
                  </div>
                  <Title level={4} className="feature-title">
                    {feature.title}
                  </Title>
                  <Paragraph className="feature-description">
                    {feature.description}
                  </Paragraph>
                </Card>
              </motion.div>
            </Col>
          ))}
        </Row>
      </motion.div>

      {/* Statistics Overview */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="stats-section"
        >
          <Row gutter={[24, 24]}>
            {/* Package Manager Distribution */}
            <Col xs={24} lg={12}>
              <Card
                title={
                  <span>
                    <GlobalOutlined style={{ marginRight: 8 }} />
                    Package Manager Distribution
                  </span>
                }
                className="stats-card"
              >
                <Spin spinning={isLoading}>
                  <div className="package-manager-stats">
                    {packageManagers.map((pm, index) => (
                      <div key={index} className="pm-stat-item">
                        <div className="pm-info">
                          <Tag color={pm.color} className="pm-tag">
                            {pm.name}
                          </Tag>
                          <Text strong>{pm.count.toLocaleString()}</Text>
                        </div>
                        <Progress
                          percent={Math.round((pm.count / (stats?.total_threats || 1)) * 100)}
                          strokeColor={pm.color}
                          showInfo={false}
                          size="small"
                        />
                      </div>
                    ))}
                  </div>
                </Spin>
              </Card>
            </Col>

            {/* Recent Threat Updates */}
            <Col xs={24} lg={12}>
              <Card
                title={
                  <span>
                    <ClockCircleOutlined style={{ marginRight: 8 }} />
                    Recent Threat Updates
                  </span>
                }
                className="stats-card"
                extra={
                  <Button
                    type="link"
                    size="small"
                    onClick={() => navigate('/threats')}
                  >
                    View All
                  </Button>
                }
              >
                <Spin spinning={isLoading}>
                  <List
                    dataSource={stats?.recent_updates?.slice(0, 5) || []}
                    renderItem={(item) => (
                      <List.Item className="recent-threat-item">
                        <List.Item.Meta
                          avatar={
                            <Avatar
                              icon={<BugOutlined />}
                              style={{ backgroundColor: '#ff4d4f' }}
                              size="small"
                            />
                          }
                          title={
                            <div className="threat-title">
                              <Text strong ellipsis style={{ maxWidth: 200 }}>
                                {item.package_name}
                              </Text>
                              <Badge
                                color={
                                  item.metadata?.confidence_level === 'high' ? '#52c41a' :
                                  item.metadata?.confidence_level === 'medium' ? '#faad14' : '#ff4d4f'
                                }
                                text={item.metadata?.confidence_level || 'Unknown'}
                                size="small"
                              />
                            </div>
                          }
                          description={
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {dayjs(item.metadata?.last_updated).format('MMM DD, YYYY')}
                            </Text>
                          }
                        />
                      </List.Item>
                    )}
                    locale={{
                      emptyText: 'No recent updates available'
                    }}
                  />
                </Spin>
              </Card>
            </Col>
          </Row>
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="quick-actions-section"
      >
        <Card className="quick-actions-card">
          <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>
            Quick Actions
          </Title>
          <Row gutter={[24, 16]} justify="center">
            <Col xs={24} sm={12} md={6}>
              <Button
                type="primary"
                size="large"
                block
                icon={<SearchOutlined />}
                onClick={() => navigate('/search')}
                className="quick-action-btn"
              >
                Advanced Search
              </Button>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Button
                size="large"
                block
                icon={<DatabaseOutlined />}
                onClick={() => navigate('/threats')}
                className="quick-action-btn"
              >
                Browse Threats
              </Button>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Button
                size="large"
                block
                icon={<BarChartOutlined />}
                onClick={() => navigate('/statistics')}
                className="quick-action-btn"
              >
                View Statistics
              </Button>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Button
                size="large"
                block
                icon={<RocketOutlined />}
                onClick={() => window.open('/api/docs', '_blank')}
                className="quick-action-btn"
              >
                API Docs
              </Button>
            </Col>
          </Row>
        </Card>
      </motion.div>
    </div>
  )
}

export default HomePage
