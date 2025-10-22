import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Typography,
  Tag,
  Button,
  Spin,
  Alert,
  Row,
  Col,
  Divider,
  List,
  Timeline,
  Space,
  Tooltip,
  Progress,
  Badge,
  Descriptions,
  Statistic,
  Empty,
  message
} from 'antd'
import {
  ArrowLeftOutlined,
  ShieldOutlined,
  BugOutlined,
  CalendarOutlined,
  LinkOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  ExclamationCircleOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  UserOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  EyeOutlined,
  TagOutlined,
  AimOutlined,
  ThunderboltOutlined,
  SecurityScanOutlined,
  BookOutlined,
  FileTextOutlined,
  FireOutlined,
  CodeOutlined
} from '@ant-design/icons'
import { getThreatDetail } from '../services/api'
import './ThreatDetail.css'

const { Title, Text, Paragraph } = Typography

const ThreatDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [threat, setThreat] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchThreatDetail = async () => {
      if (!id) {
        setError('No threat ID provided')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        const response = await getThreatDetail(id)
        setThreat(response)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch threat detail:', err)
        setError('Failed to load threat details')
        message.error('Failed to load threat details')
      } finally {
        setLoading(false)
      }
    }

    fetchThreatDetail()
  }, [id])

  // Helper functions
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Invalid date'
    }
  }

  const getConfidenceColor = (level) => {
    const colors = {
      high: '#52c41a',
      medium: '#faad14',
      low: '#ff4d4f'
    }
    return colors[level] || '#d9d9d9'
  }

  const getPackageManagerColor = (manager) => {
    const colors = {
      pypi: '#3776ab',
      npm: '#cb3837',
      maven: '#f89820',
      nuget: '#004880',
      gem: '#701516',
      go: '#00add8'
    }
    return colors[manager] || '#666'
  }

  const renderRepositoryLinks = (urls) => {
    if (!urls || urls.length === 0) return <Text type="secondary">No repository links available</Text>
    
    return (
      <List
        size="small"
        dataSource={urls}
        renderItem={(url, index) => (
          <List.Item key={index} style={{ padding: '8px 0', borderBottom: 'none' }}>
            <Space style={{ width: '100%', alignItems: 'flex-start' }}>
              <LinkOutlined style={{ color: '#1890ff', marginTop: '2px', flexShrink: 0 }} />
              <Tooltip title={url}>
                <a 
                  href={url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ 
                    color: '#1890ff',
                    wordBreak: 'break-all',
                    lineHeight: '1.5'
                  }}
                >
                  {url}
                </a>
              </Tooltip>
            </Space>
          </List.Item>
        )}
      />
    )
  }

  const renderDiscoveryTimeline = (sources) => {
    if (!sources || sources.length === 0) {
      return <Empty description="No discovery timeline available" />
    }

    const sortedSources = [...sources].sort((a, b) => 
      new Date(b.discovery_date) - new Date(a.discovery_date)
    )

    return (
      <Timeline mode="left">
        {sortedSources.map((source, index) => (
          <Timeline.Item
            key={index}
            color="#1890ff"
            label={formatDate(source.discovery_date)}
          >
            <Space direction="vertical" size={4}>
              <Text strong style={{ color: '#1890ff' }}>{source.data_source}</Text>
              {source.discoverer && (
                <Text type="secondary">
                  <UserOutlined /> {Array.isArray(source.discoverer) ? source.discoverer.join(', ') : source.discoverer}
                </Text>
              )}
              {source.source_link && (
                <a href={source.source_link} target="_blank" rel="noopener noreferrer">
                  <LinkOutlined /> View Source
                </a>
              )}
            </Space>
          </Timeline.Item>
        ))}
      </Timeline>
    )
  }

  if (loading) {
    return (
      <div className="threat-detail">
        <div className="loading-container">
          <Spin size="large" />
        </div>
      </div>
    )
  }

  if (error || !threat) {
    return (
      <div className="threat-detail">
        <div className="error-container">
          <Card className="error-card">
            <Alert
              message="Error"
              description={error || 'Threat not found'}
              type="error"
              showIcon
              action={
                <Button type="primary" onClick={() => navigate('/database')}>
                  Back to Database
                </Button>
              }
            />
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="threat-detail">
      {/* Header */}
      <div className="detail-header">
        <Space align="center">
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/database')}
            style={{ color: 'white' }}
          >
            Back to Database
          </Button>
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            🛡️ Threat Intelligence Details
          </Title>
        </Space>
      </div>

      <div className="detail-content">
        <Row gutter={[24, 24]}>
          {/* Main Content */}
          <Col xs={24} lg={16}>
            {/* Package Overview */}
            <Card className="overview-card" title={
              <Space>
                <DatabaseOutlined />
                Package Overview
              </Space>
            }>
              <div className="threat-header">
                <div>
                  <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                    {threat.package_name}
                  </Title>
                  <Space style={{ marginTop: 8 }}>
                    <Tag 
                      color={getPackageManagerColor(threat.package_manager)}
                      style={{ fontSize: '14px', padding: '4px 12px' }}
                    >
                      {threat.package_manager?.toUpperCase()}
                    </Tag>
                    <Tag 
                      color={getConfidenceColor(threat.metadata?.confidence_level)}
                      style={{ fontSize: '14px', padding: '4px 12px' }}
                    >
                      {threat.metadata?.confidence_level?.toUpperCase() || 'UNKNOWN'} CONFIDENCE
                    </Tag>
                  </Space>
                </div>
                <div className="threat-icon">
                  <WarningOutlined />
                </div>
              </div>

              {/* Package Versions */}
              {threat.package_versions && threat.package_versions.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    <TagOutlined /> Affected Versions:
                  </Text>
                  <div className="versions-grid">
                    {threat.package_versions.map((version, index) => (
                      <Tag key={index} style={{ 
                        fontFamily: 'Monaco, Menlo, monospace',
                        fontSize: '13px',
                        padding: '4px 8px'
                      }}>
                        {version}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Threat Information */}
            <Card className="section-card" title={
              <Space>
                <BugOutlined />
                Threat Information
              </Space>
            }>
              <Descriptions column={1} size="middle">
                {/* Attack Methods */}
                {threat.threat_info?.attack_methods && threat.threat_info.attack_methods.length > 0 && (
                  <Descriptions.Item label={
                    <Space><ThunderboltOutlined /> Attack Methods</Space>
                  }>
                    <div style={{ lineHeight: '1.6' }}>
                      {threat.threat_info.attack_methods.map((method, index) => (
                        <Paragraph key={index} style={{ margin: '8px 0', fontSize: '14px' }}>
                          {method}
                        </Paragraph>
                      ))}
                    </div>
                  </Descriptions.Item>
                )}

                {/* Attack Vectors */}
                {threat.threat_info?.attack_vectors && threat.threat_info.attack_vectors.length > 0 && (
                  <Descriptions.Item label={
                    <Space><AimOutlined /> Attack Vectors</Space>
                  }>
                    <div style={{ lineHeight: '1.6' }}>
                      {threat.threat_info.attack_vectors.map((vector, index) => (
                        <Paragraph key={index} style={{ margin: '8px 0', fontSize: '14px' }}>
                          {vector}
                        </Paragraph>
                      ))}
                    </div>
                  </Descriptions.Item>
                )}

                {/* Targets */}
                {threat.threat_info?.targets && threat.threat_info.targets.length > 0 && (
                  <Descriptions.Item label={
                    <Space><EyeOutlined /> Targets</Space>
                  }>
                    <Space wrap>
                      {threat.threat_info.targets.map((target, index) => (
                        <Tag key={index} color="orange">
                          {target}
                        </Tag>
                      ))}
                    </Space>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            {/* Indicators of Compromise */}
            {threat.indicators_of_compromise && threat.indicators_of_compromise.length > 0 && (
              <Card className="section-card" title={
                <Space>
                  <SecurityScanOutlined />
                  Indicators of Compromise
                </Space>
              }>
                <List
                  size="small"
                  dataSource={threat.indicators_of_compromise}
                  renderItem={(ioc, index) => (
                    <List.Item key={index}>
                      <Space>
                        <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                        <Text>{ioc}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* Patch Information */}
            {threat.patch_info && (
              <Card className="section-card" title={
                <Space>
                  <SafetyCertificateOutlined />
                  Patch Information
                </Space>
              }>
                <Descriptions column={1}>
                  {threat.patch_info.fix_method && (
                    <Descriptions.Item label="Fix Method">
                      <Text>{threat.patch_info.fix_method}</Text>
                    </Descriptions.Item>
                  )}
                  {threat.patch_info.patch_version && (
                    <Descriptions.Item label="Patch Version">
                      <Tag color="green">{threat.patch_info.patch_version}</Tag>
                    </Descriptions.Item>
                  )}
                  {threat.patch_info.patch_url && (
                    <Descriptions.Item label="Patch URL">
                      <a href={threat.patch_info.patch_url} target="_blank" rel="noopener noreferrer">
                        {threat.patch_info.patch_url}
                      </a>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            )}

            {/* References */}
            {threat.references && threat.references.length > 0 && (
              <Card className="section-card" title={
                <Space>
                  <BookOutlined />
                  References
                </Space>
              }>
                <List
                  size="small"
                  dataSource={threat.references}
                  renderItem={(ref, index) => (
                    <List.Item key={index}>
                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        <a href={ref.url} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all' }}>
                          {ref.url}
                        </a>
                        {ref.type && <Tag>{ref.type}</Tag>}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* Discovery Timeline */}
            <Card className="section-card" title={
              <Space>
                <ClockCircleOutlined />
                Discovery Timeline
              </Space>
            }>
              {renderDiscoveryTimeline(threat.credit?.sources)}
            </Card>
          </Col>

          {/* Sidebar */}
          <Col xs={24} lg={8}>
            {/* Metadata */}
            <Card title={<><InfoCircleOutlined /> Metadata</> } className="sidebar-card">
              <div className="metadata-item">
                <Text strong>Threat ID:</Text>
                <br />
                <Text code>{threat.id}</Text>
              </div>
              <Divider />
              <div className="metadata-item">
                <Text strong>Data Quality Score:</Text>
                <br />
                <Progress 
                  percent={Math.round((threat.metadata?.data_quality_score || 0) * 100)} 
                  size="small"
                  status={threat.metadata?.data_quality_score > 0.7 ? 'success' : 
                         threat.metadata?.data_quality_score > 0.4 ? 'normal' : 'exception'}
                />
                <Text type="secondary">
                  {threat.metadata?.data_quality_score?.toFixed(2) || 'N/A'}
                </Text>
              </div>
              <Divider />
              <div className="metadata-item">
                <Text strong>Created:</Text>
                <br />
                <Text>{formatDate(threat.metadata?.created_at)}</Text>
              </div>
              <Divider />
              <div className="metadata-item">
                <Text strong>Last Updated:</Text>
                <br />
                <Text>{formatDate(threat.metadata?.last_updated)}</Text>
              </div>
              <Divider />
              <div className="metadata-item">
                <Text strong>Data Collected:</Text>
                <br />
                <Text>{formatDate(threat.credit?.collected_at)}</Text>
              </div>
            </Card>

            {/* Repository Links */}
            <Card title={<><LinkOutlined /> Repository Links</> } className="sidebar-card">
              <div style={{ wordBreak: 'break-all' }}>
                {renderRepositoryLinks(threat.repository_url)}
              </div>
            </Card>

            {/* Data Sources */}
            {threat.credit?.sources && threat.credit.sources.length > 0 && (
              <Card title={<><GlobalOutlined /> Data Sources</> } className="sidebar-card">
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                  {threat.credit.sources.map((source, index) => (
                    <div key={index} style={{ 
                      padding: '8px 12px', 
                      background: '#f8f9fa', 
                      borderRadius: '6px',
                      border: '1px solid #e9ecef'
                    }}>
                      <Space direction="vertical" size={2}>
                        <Text strong style={{ color: '#1890ff' }}>
                          {source.data_source}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {formatDate(source.discovery_date)}
                        </Text>
                      </Space>
                    </div>
                  ))}
                </Space>
              </Card>
            )}

            {/* Statistics */}
            <Card title={<><FileTextOutlined /> Statistics</> } className="sidebar-card">
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic 
                    title="References" 
                    value={threat.references?.length || 0}
                    prefix={<BookOutlined />}
                  />
                </Col>
                <Col span={12}>
                  <Statistic 
                    title="Sources" 
                    value={threat.credit?.sources?.length || 0}
                    prefix={<DatabaseOutlined />}
                  />
                </Col>
                <Col span={12} style={{ marginTop: 16 }}>
                  <Statistic 
                    title="Attack Methods" 
                    value={threat.threat_info?.attack_methods?.length || 0}
                    prefix={<ThunderboltOutlined />}
                  />
                </Col>
                <Col span={12} style={{ marginTop: 16 }}>
                  <Statistic 
                    title="IoCs" 
                    value={threat.indicators_of_compromise?.length || 0}
                    prefix={<SecurityScanOutlined />}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  )
}

export default ThreatDetail