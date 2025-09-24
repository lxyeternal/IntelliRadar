import React from 'react'
import { useQuery } from 'react-query'
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Alert,
  Spin,
  Progress,
  Tag,
  List
} from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  BugOutlined,
  DatabaseOutlined,
  SecurityScanOutlined,
  ClockCircleOutlined,
  FireOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell,
  LineChart,
  Line,
  ResponsiveContainer
} from 'recharts'
import dayjs from 'dayjs'
import { getStatistics } from '../services/api'
import './Statistics.css'

const { Title, Text } = Typography

// Color configuration
const COLORS = {
  primary: '#667eea',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
  info: '#1890ff'
}

// Package manager color mapping
const PACKAGE_MANAGER_COLORS = {
  npm: '#cb3837',
  pypi: '#3776ab',
  maven: '#f89820',
  nuget: '#004880',
  cargo: '#000000',
  gem: '#cc342d'
}

// Confidence level color mapping
const CONFIDENCE_COLORS = {
  high: '#52c41a',
  medium: '#faad14',
  low: '#ff4d4f'
}

const Statistics = () => {
  // Get statistics data
  const {
    data: stats,
    isLoading,
    error,
    refetch
  } = useQuery('statistics', getStatistics, {
    refetchInterval: 60000 // Refresh every 1 minute
  })

  if (isLoading) {
    return (
      <div className="statistics-loading">
        <Spin size="large" tip="Loading statistics data..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="statistics-error">
        <Alert
          message="Failed to Load Statistics Data"
          description="Unable to retrieve statistics information. Please check your network connection or try again later."
          type="error"
          showIcon
          action={
            <button onClick={() => refetch()}>Retry</button>
          }
        />
      </div>
    )
  }

  // Prepare chart data
  const packageManagerData = stats?.package_managers?.map(pm => ({
    name: pm.name.toUpperCase(),
    value: pm.count,
    color: PACKAGE_MANAGER_COLORS[pm.name] || '#666'
  })) || []

  const confidenceData = Object.entries(stats?.confidence_distribution || {}).map(([level, count]) => ({
    name: level === 'high' ? 'High' : level === 'medium' ? 'Medium' : 'Low',
    value: count,
    color: CONFIDENCE_COLORS[level] || '#666'
  }))

  const attackMethodsData = Object.entries(stats?.attack_methods_stats || {})
    .slice(0, 10)
    .map(([method, count]) => ({
      method: method.length > 20 ? `${method.substring(0, 20)}...` : method,
      count
    }))

  // Simulate monthly trend data
  const monthlyTrends = Array.from({ length: 6 }, (_, i) => {
    const date = dayjs().subtract(5 - i, 'month')
    return {
      month: date.format('MMM'),
      threats: Math.floor(Math.random() * 50) + 20
    }
  })

  return (
    <div className="statistics-page">
      {/* Page title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="statistics-header"
      >
        <div className="statistics-header-content">
          <Title level={1} className="statistics-title">
            <BarChartOutlined className="statistics-title-icon" />
            Statistics Analysis
          </Title>
          <Text className="statistics-description">
            Multi-dimensional statistical analysis of threat intelligence data, insights into security threat trends and distribution
          </Text>
        </div>
      </motion.div>

      {/* Core metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Row gutter={[24, 24]} className="core-metrics">
          <Col xs={24} sm={12} lg={6}>
            <Card className="metric-card danger">
              <Statistic
                title="Total Threats"
                value={stats?.total_threats || 0}
                prefix={<BugOutlined />}
                valueStyle={{ color: COLORS.error }}
suffix="items"
              />
              <div className="metric-trend">
                <Text type="secondary">Real-time monitoring</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="metric-card info">
              <Statistic
                title="Package Managers"
                value={stats?.package_managers?.length || 0}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: COLORS.info }}
                suffix="types"
              />
              <div className="metric-trend">
                <Text type="secondary">Major platforms covered</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="metric-card warning">
              <Statistic
                title="Data Sources"
                value={stats?.crawler_stats?._summary?.total_sources || 19}
                prefix={<SecurityScanOutlined />}
                valueStyle={{ color: COLORS.warning }}
suffix="items"
              />
              <div className="metric-trend">
                <Text type="secondary">Authoritative intelligence</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="metric-card success">
              <Statistic
                title="Today's Updates"
                value={stats?.recent_updates?.length || 0}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: COLORS.success }}
                suffix="items"
              />
              <div className="metric-trend">
                <Text type="secondary">Continuously updating</Text>
              </div>
            </Card>
          </Col>
        </Row>
      </motion.div>

      <Row gutter={[24, 24]}>
        {/* Package Manager Distribution */}
        <Col xs={24} lg={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card 
              title={
                <span>
                  <PieChartOutlined /> Package Manager Distribution
                </span>
              }
              className="chart-card"
            >
              {packageManagerData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={packageManagerData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {packageManagerData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-empty">No data available</div>
              )}
              
              <div className="chart-legend">
                {packageManagerData.map((item, index) => (
                  <div key={index} className="legend-item">
                    <div 
                      className="legend-color" 
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <Text>{item.name}: {item.value}</Text>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        </Col>

        {/* Confidence Distribution */}
        <Col xs={24} lg={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card 
              title={
                <span>
                  <TrophyOutlined /> Confidence Distribution
                </span>
              }
              className="chart-card"
            >
              <div className="confidence-chart">
                {confidenceData.map((item, index) => {
                  const total = confidenceData.reduce((sum, d) => sum + d.value, 0)
                  const percentage = total > 0 ? (item.value / total * 100).toFixed(1) : 0
                  
                  return (
                    <div key={index} className="confidence-item">
                      <div className="confidence-header">
                        <Text strong>{item.name} Confidence</Text>
                        <Text>{item.value} items</Text>
                      </div>
                      <Progress
                        percent={percentage}
                        strokeColor={item.color}
                        showInfo={false}
                        className="confidence-progress"
                      />
                      <Text type="secondary">{percentage}%</Text>
                    </div>
                  )
                })}
              </div>
            </Card>
          </motion.div>
        </Col>

        {/* Attack Methods Statistics */}
        <Col xs={24}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card 
              title={
                <span>
                  <FireOutlined /> Top 10 Attack Methods
                </span>
              }
              className="chart-card"
            >
              {attackMethodsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={attackMethodsData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="method" 
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      interval={0}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar 
                      dataKey="count" 
                      fill={COLORS.primary}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-empty">No data available</div>
              )}
            </Card>
          </motion.div>
        </Col>

        {/* Threat Trends */}
        <Col xs={24} lg={16}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card 
              title={
                <span>
                  <BarChartOutlined /> Threat Discovery Trends
                </span>
              }
              className="chart-card"
            >
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={monthlyTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="threats" 
                    stroke={COLORS.primary}
                    strokeWidth={3}
                    dot={{ fill: COLORS.primary, strokeWidth: 2, r: 6 }}
                    name="Threats"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>
        </Col>

        {/* Recent Threats */}
        <Col xs={24} lg={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card 
              title={
                <span>
                  <ClockCircleOutlined /> Recently Discovered Threats
                </span>
              }
              className="chart-card recent-threats-card"
            >
              <List
                dataSource={stats?.recent_updates?.slice(0, 8) || []}
                renderItem={(threat, index) => (
                  <List.Item key={index} className="recent-threat-item">
                    <div className="threat-info">
                      <div className="threat-name">
                        <Text strong>{threat.package_name}</Text>
                        <Tag 
                          color={PACKAGE_MANAGER_COLORS[threat.package_manager] || '#666'}
                          size="small"
                        >
                          {threat.package_manager?.toUpperCase()}
                        </Tag>
                      </div>
                      <Text type="secondary" className="threat-time">
                        {dayjs(threat.metadata?.last_updated).fromNow()}
                      </Text>
                    </div>
                  </List.Item>
                )}
                locale={{ emptyText: 'No recent threats' }}
              />
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}

export default Statistics
