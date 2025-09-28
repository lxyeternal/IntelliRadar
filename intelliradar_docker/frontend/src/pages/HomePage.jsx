import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Button, Typography, Space, Progress, Tag, List, Timeline, Table } from 'antd'
import { Link } from 'react-router-dom'
import { 
  DatabaseOutlined, 
  SafetyOutlined, 
  WarningOutlined, 
  TrophyOutlined,
  ArrowRightOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
  FireOutlined,
  SafetyCertificateOutlined,
  BugOutlined,
  SearchOutlined,
  BarChartOutlined,
  EyeOutlined,
  SecurityScanOutlined
} from '@ant-design/icons'
import { getStatistics, getLatestThreats } from '../services/api'
import './HomePage.css'

const { Title, Paragraph, Text } = Typography

const HomePage = () => {
  const [statistics, setStatistics] = useState({
    total_threats: 0,
    package_managers: [],
    confidence_distribution: {},
    data_sources: []
  })
  const [latestPackages, setLatestPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const [latestPackagesLoading, setLatestPackagesLoading] = useState(true)

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        const data = await getStatistics()
        setStatistics(data)
      } catch (error) {
        console.error('Failed to fetch statistics:', error)
      } finally {
        setLoading(false)
      }
    }

    const fetchLatestPackages = async () => {
      try {
        const data = await getLatestThreats()
        setLatestPackages(data.latest_packages || [])
      } catch (error) {
        console.error('Failed to fetch latest packages:', error)
      } finally {
        setLatestPackagesLoading(false)
      }
    }

    fetchStatistics()
    fetchLatestPackages()
  }, [])

  const getHighConfidenceCount = () => {
    return statistics.confidence_distribution?.high || 0
  }

  const getMediumConfidenceCount = () => {
    return statistics.confidence_distribution?.medium || 0
  }

  const getDataSourcesCount = () => {
    return statistics.data_sources?.length || 0
  }

  const getLowConfidenceCount = () => {
    return statistics.confidence_distribution?.low || 0
  }

  const getTopPackageManagers = () => {
    if (!statistics.package_managers) return []
    return statistics.package_managers.slice(0, 5).map(pm => ({
      name: pm._id,
      count: pm.count,
      percentage: Math.round((pm.count / statistics.total_threats) * 100)
    }))
  }

  const getTopDataSources = () => {
    if (!statistics.data_sources) return []
    return statistics.data_sources.slice(0, 5).map(ds => ({
      name: ds._id,
      count: ds.count,
      percentage: Math.round((ds.count / statistics.total_threats) * 100)
    }))
  }

  const getRecentThreatsCount = () => {
    // Assuming we have recent threats data
    return statistics.recent_threats_count || Math.floor(statistics.total_threats * 0.15)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getConfidenceColor = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high': return '#52c41a'
      case 'medium': return '#faad14'
      case 'low': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const getPackageManagerColor = (pm) => {
    const colors = {
      'pypi': '#3776ab',
      'npm': '#cb3837',
      'maven': '#f58220',
      'nuget': '#004880',
      'rubygems': '#cc342d',
      'packagist': '#777bb4',
      'crates.io': '#ce422b',
      'go': '#00add8'
    }
    return colors[pm?.toLowerCase()] || '#1890ff'
  }

  return (
    <div className="homepage">
      <div className="hero-section">
        <div className="hero-content">
          <Title level={1} className="hero-title">
            🛡️ IntelliRadar
          </Title>
          <Title level={2} className="hero-subtitle">
            Malicious Package Intelligence Platform
          </Title>
          <Paragraph className="hero-description">
            Comprehensive threat intelligence database for malicious packages across 
            multiple package managers. Stay protected with real-time security insights 
            and detailed vulnerability information.
          </Paragraph>
          <Space size="large" className="hero-actions">
            <Link to="/database">
              <Button type="primary" size="large" icon={<DatabaseOutlined />}>
                Explore Database
                <ArrowRightOutlined />
              </Button>
            </Link>
          </Space>
        </div>
      </div>

      <div className="stats-section">
        <Row gutter={[24, 24]}>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card" loading={loading}>
              <Statistic
                title="Total Threats"
                value={statistics.total_threats}
                prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f', fontSize: '32px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card" loading={loading}>
              <Statistic
                title="High Confidence"
                value={getHighConfidenceCount()}
                prefix={<SafetyOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontSize: '32px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card" loading={loading}>
              <Statistic
                title="Recent Threats"
                value={getRecentThreatsCount()}
                prefix={<FireOutlined style={{ color: '#fa541c' }} />}
                valueStyle={{ color: '#fa541c', fontSize: '32px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card" loading={loading}>
              <Statistic
                title="Data Sources"
                value={getDataSourcesCount()}
                prefix={<GlobalOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff', fontSize: '32px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        </Row>
      </div>

      <div className="detailed-stats-section">
        <Row gutter={[24, 24]}>
          {/* Confidence Distribution */}
          <Col xs={24} lg={8}>
            <Card 
              title={<><SafetyCertificateOutlined /> Confidence Distribution</>} 
              className="detail-card"
              loading={loading}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Text strong style={{ color: '#52c41a' }}>High Confidence</Text>
                    <Text>{getHighConfidenceCount()}</Text>
                  </div>
                  <Progress 
                    percent={Math.round((getHighConfidenceCount() / statistics.total_threats) * 100)} 
                    strokeColor="#52c41a"
                    showInfo={false}
                  />
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Text strong style={{ color: '#faad14' }}>Medium Confidence</Text>
                    <Text>{getMediumConfidenceCount()}</Text>
                  </div>
                  <Progress 
                    percent={Math.round((getMediumConfidenceCount() / statistics.total_threats) * 100)} 
                    strokeColor="#faad14"
                    showInfo={false}
                  />
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Text strong style={{ color: '#ff4d4f' }}>Low Confidence</Text>
                    <Text>{getLowConfidenceCount()}</Text>
                  </div>
                  <Progress 
                    percent={Math.round((getLowConfidenceCount() / statistics.total_threats) * 100)} 
                    strokeColor="#ff4d4f"
                    showInfo={false}
                  />
                </div>
              </Space>
            </Card>
          </Col>

          {/* Top Package Managers */}
          <Col xs={24} lg={8}>
            <Card 
              title={<><DatabaseOutlined /> Top Package Managers</>} 
              className="detail-card"
              loading={loading}
            >
              <List
                size="small"
                dataSource={getTopPackageManagers()}
                renderItem={(item) => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                      <Space>
                        <Tag color="blue">{item.name?.toUpperCase()}</Tag>
                      </Space>
                      <Space>
                        <Text strong>{item.count}</Text>
                        <Text type="secondary">({item.percentage}%)</Text>
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          </Col>

          {/* Top Data Sources */}
          <Col xs={24} lg={8}>
            <Card 
              title={<><GlobalOutlined /> Top Data Sources</>} 
              className="detail-card"
              loading={loading}
            >
              <List
                size="small"
                dataSource={getTopDataSources()}
                renderItem={(item) => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                      <Space>
                        <Tag color="green">{item.name}</Tag>
                      </Space>
                      <Space>
                        <Text strong>{item.count}</Text>
                        <Text type="secondary">({item.percentage}%)</Text>
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Latest Malicious Packages */}
      <div className="latest-packages-section">
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FireOutlined style={{ color: '#ff4d4f' }} />
              <span>Latest Malicious Packages</span>
            </div>
          }
          className="latest-packages-card"
          loading={latestPackagesLoading}
        >
          <Table
            dataSource={latestPackages}
            rowKey="id"
            pagination={false}
            size="middle"
            className="latest-packages-table"
            columns={[
              {
                title: 'Package Name',
                dataIndex: 'package_name',
                key: 'package_name',
                render: (name, record) => (
                  <Link 
                    to={`/threats/${record.id}`}
                    className="package-name-link"
                  >
                    {name}
                  </Link>
                ),
                width: '25%',
              },
              {
                title: 'Package Manager',
                dataIndex: 'package_manager',
                key: 'package_manager',
                render: (pm) => (
                  <Tag 
                    color={getPackageManagerColor(pm)}
                    className="package-manager-tag"
                  >
                    {pm?.toUpperCase()}
                  </Tag>
                ),
                width: '15%',
                align: 'center',
              },
              {
                title: 'Version',
                dataIndex: 'version',
                key: 'version',
                render: (version) => {
                  if (!version || version === 'Unknown') {
                    return <Text type="secondary">N/A</Text>;
                  }
                  // 如果是数组，直接转换成字符串显示整个列表
                  if (Array.isArray(version)) {
                    return <Text code>{JSON.stringify(version)}</Text>;
                  }
                  // 如果是字符串，直接显示
                  return <Text code>{version}</Text>;
                },
                width: '20%',
                align: 'left',
              },
              {
                title: 'Confidence',
                dataIndex: 'confidence_level',
                key: 'confidence_level',
                render: (confidence) => (
                  <Tag 
                    color={getConfidenceColor(confidence)}
                    className="confidence-tag"
                  >
                    {confidence?.toUpperCase() || 'UNKNOWN'}
                  </Tag>
                ),
                width: '15%',
                align: 'center',
              },
              {
                title: 'Last Updated',
                dataIndex: 'collected_time',
                key: 'collected_time',
                render: (time) => (
                  <Space>
                    <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
                    <Text type="secondary">{formatDate(time)}</Text>
                  </Space>
                ),
                width: '20%',
                align: 'center',
              },
              {
                title: 'Action',
                key: 'action',
                render: (_, record) => (
                  <Link to={`/threats/${record.id}`}>
                    <Button type="link" size="small" icon={<EyeOutlined />}>
                      View
                    </Button>
                  </Link>
                ),
                width: '10%',
                align: 'center',
              },
            ]}
            locale={{
              emptyText: latestPackagesLoading ? 'Loading...' : 'No recent packages found'
            }}
          />
          <div style={{ textAlign: 'center', marginTop: '16px' }}>
            <Link to="/database">
              <Button type="primary" icon={<DatabaseOutlined />}>
                View All Packages
                <ArrowRightOutlined />
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      <div className="features-section">
        <Row gutter={[32, 32]} justify="center" className="features-row">
          <Col xs={24} sm={12} lg={7} className="features-col">
            <Card className="feature-card" hoverable>
              <div className="feature-icon">
                <DatabaseOutlined />
              </div>
              <Title level={3}>Comprehensive Database</Title>
              <Paragraph>
                Access detailed information about malicious packages across multiple 
                package managers including PyPI, npm, Maven, and more.
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={7} className="features-col">
            <Card className="feature-card" hoverable>
              <div className="feature-icon">
                <SafetyOutlined />
              </div>
              <Title level={3}>Real-time Intelligence</Title>
              <Paragraph>
                Stay updated with the latest threat intelligence from multiple security 
                sources and research organizations.
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={7} className="features-col">
            <Card className="feature-card" hoverable>
              <div className="feature-icon">
                <WarningOutlined />
              </div>
              <Title level={3}>Advanced Filtering</Title>
              <Paragraph>
                Filter threats by package manager, confidence level, date range, and data 
                source to find exactly what you need.
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  )
}

export default HomePage