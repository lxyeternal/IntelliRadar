import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Timeline,
  Alert,
  Spin,
  Row,
  Col,
  Typography,
  Divider,
  Badge,
  Tooltip,
  List,
  Collapse,
  Statistic,
  Progress
} from 'antd'
import {
  ArrowLeftOutlined,
  ExclamationCircleOutlined,
  LinkOutlined,
  ClockCircleOutlined,
  SecurityScanOutlined,
  BugOutlined,
  EyeOutlined,
  CopyOutlined,
  DownloadOutlined,
  GlobalOutlined,
  WarningOutlined,
  CodeOutlined,
  FireOutlined,
  DatabaseOutlined,
  AimOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import copy from 'copy-to-clipboard'
import { message } from 'antd'
import { fetchThreatDetail } from '../services/api'
import './ThreatDetail.css'

const { Title, Paragraph, Text } = Typography
const { Panel } = Collapse

// Package manager configuration
const PACKAGE_MANAGERS = {
  npm: { color: '#cb3837', label: 'NPM' },
  pypi: { color: '#3776ab', label: 'PyPI' },
  maven: { color: '#f89820', label: 'Maven' },
  nuget: { color: '#004880', label: 'NuGet' },
  cargo: { color: '#000000', label: 'Cargo' },
  gem: { color: '#cc342d', label: 'RubyGems' }
}

// Confidence level configuration
const CONFIDENCE_LEVELS = {
  high: { color: '#52c41a', label: 'High Confidence', icon: '🟢' },
  medium: { color: '#faad14', label: 'Medium Confidence', icon: '🟡' },
  low: { color: '#ff4d4f', label: 'Low Confidence', icon: '🔴' }
}

const ThreatDetail = () => {
  const { threatId } = useParams()
  const navigate = useNavigate()

  // Get threat details
  const {
    data: threat,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['threat-detail', threatId],
    () => fetchThreatDetail(threatId),
    {
      enabled: !!threatId,
      retry: 2
    }
  )

  // Copy to clipboard
  const copyToClipboard = (text, label) => {
    copy(text)
    message.success(`${label} copied to clipboard`)
  }

  // Open link
  const openLink = (url) => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  if (isLoading) {
    return (
      <div className="threat-detail-loading">
        <Spin size="large" tip="Loading threat details..." />
      </div>
    )
  }

  if (error || !threat) {
    return (
      <div className="threat-detail-error">
        <Alert
          message="Failed to Load Threat Details"
          description="Unable to retrieve threat information. Please check if the threat ID is correct or try again later."
          type="error"
          showIcon
          action={
            <Space>
              <Button onClick={() => navigate('/threats')}>
                Back to List
              </Button>
              <Button type="primary" onClick={() => refetch()}>
                Retry
              </Button>
            </Space>
          }
        />
      </div>
    )
  }

  const packageManager = PACKAGE_MANAGERS[threat.package_manager] || { 
    color: '#666', 
    label: threat.package_manager 
  }
  
  const confidenceLevel = CONFIDENCE_LEVELS[threat.metadata?.confidence_level] || {
    color: '#666',
    label: threat.metadata?.confidence_level || 'Unknown',
    icon: '❓'
  }

  const qualityScore = threat.metadata?.data_quality_score ? 
    Math.round(threat.metadata.data_quality_score * 100) : 0

  return (
    <div className="threat-detail">
      {/* Back button */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="back-button-wrapper"
      >
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/threats')}
          className="back-button"
          size="large"
        >
          Back to Threat Database
        </Button>
      </motion.div>

      {/* Threat overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="threat-overview-card">
          <div className="threat-header">
            <div className="threat-title-section">
              <Title level={1} className="threat-title">
                <BugOutlined className="threat-icon" />
                {threat.package_name}
              </Title>
              <div className="threat-meta">
                <Tag color={packageManager.color} className="package-tag" icon={<DatabaseOutlined />}>
                  {packageManager.label}
                </Tag>
                <Badge
                  color={confidenceLevel.color}
                  text={`${confidenceLevel.icon} ${confidenceLevel.label}`}
                  className="confidence-badge"
                />
                <Text className="threat-id" code copyable>
                  {threat.id}
                </Text>
              </div>
              <Paragraph className="threat-description">
                Malicious package detected in {packageManager.label} repository with {confidenceLevel.label.toLowerCase()}
              </Paragraph>
            </div>
            <div className="threat-stats">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Quality Score"
                    value={qualityScore}
                    suffix="%"
                    prefix={<InfoCircleOutlined />}
                    valueStyle={{ color: qualityScore >= 70 ? '#52c41a' : qualityScore >= 40 ? '#faad14' : '#ff4d4f' }}
                  />
                  <Progress 
                    percent={qualityScore} 
                    size="small" 
                    strokeColor={qualityScore >= 70 ? '#52c41a' : qualityScore >= 40 ? '#faad14' : '#ff4d4f'}
                    showInfo={false}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Attack Methods"
                    value={threat.threat_info?.attack_methods?.length || 0}
                    prefix={<FireOutlined />}
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Affected Versions"
                    value={threat.package_versions?.length || 0}
                    prefix={<CodeOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
              </Row>
            </div>
          </div>

          {/* Basic information */}
          <Divider orientation="left">Basic Information</Divider>
          <Descriptions
            bordered
            column={{ xs: 1, sm: 2, lg: 3 }}
            className="threat-descriptions"
          >
            <Descriptions.Item label="Package Name">
              <Text strong>{threat.package_name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Package Manager">
              <Tag color={packageManager.color}>{packageManager.label}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Confidence Level">
              <Badge color={confidenceLevel.color} text={confidenceLevel.label} />
            </Descriptions.Item>
            <Descriptions.Item label="Created At">
              <Text>
                <ClockCircleOutlined /> {dayjs(threat.metadata?.created_at).format('YYYY-MM-DD HH:mm')}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Last Updated">
              <Text>
                <ClockCircleOutlined /> {dayjs(threat.metadata?.last_updated).format('YYYY-MM-DD HH:mm')}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Data Collected At">
              <Text>
                <ClockCircleOutlined /> {dayjs(threat.credit?.collected_at).format('YYYY-MM-DD HH:mm')}
              </Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </motion.div>

      <Row gutter={[24, 24]}>
        {/* Left column - Main information */}
        <Col xs={24} lg={16}>
          {/* Threat information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card title={<><SecurityScanOutlined /> Threat Analysis</>} className="section-card">
              <Collapse defaultActiveKey={['attack-methods']} className="threat-collapse">
                <Panel
                  header={
                    <Space>
                      <FireOutlined style={{ color: '#ff4d4f' }} />
                      <span>Attack Methods ({threat.threat_info?.attack_methods?.length || 0})</span>
                    </Space>
                  }
                  key="attack-methods"
                >
                  <div className="attack-methods-grid">
                    {threat.threat_info?.attack_methods?.map((method, index) => (
                      <Tag key={index} color="red" className="attack-method-tag">
                        <WarningOutlined /> {method}
                      </Tag>
                    )) || <Text type="secondary">No attack methods available</Text>}
                  </div>
                </Panel>
                <Panel
                  header={
                    <Space>
                      <AimOutlined style={{ color: '#faad14' }} />
                      <span>Attack Vectors ({threat.threat_info?.attack_vectors?.length || 0})</span>
                    </Space>
                  }
                  key="attack-vectors"
                >
                  <List
                    dataSource={threat.threat_info?.attack_vectors || []}
                    renderItem={(vector, index) => (
                      <List.Item key={index}>
                        <Text>{vector}</Text>
                      </List.Item>
                    )}
                    locale={{ emptyText: 'No attack vectors available' }}
                  />
                </Panel>
                <Panel
                  header={
                    <Space>
                      <AimOutlined style={{ color: '#1890ff' }} />
                      <span>Targets ({threat.threat_info?.targets?.length || 0})</span>
                    </Space>
                  }
                  key="targets"
                >
                  <div className="targets-grid">
                    {threat.threat_info?.targets?.map((target, index) => (
                      <Tag key={index} color="blue" className="target-tag">
                        <AimOutlined /> {target}
                      </Tag>
                    )) || <Text type="secondary">No target information available</Text>}
                  </div>
                </Panel>
              </Collapse>
            </Card>
          </motion.div>

          {/* Affected versions */}
          {threat.package_versions && threat.package_versions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card title={<><CodeOutlined /> Affected Versions</>} className="section-card">
                <div className="versions-grid">
                  {threat.package_versions.map((version, index) => (
                    <Tag key={index} color="volcano" className="version-tag">
                      <CodeOutlined /> {version}
                    </Tag>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Indicators of compromise */}
          {threat.indicators_of_compromise && threat.indicators_of_compromise.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card title={<><ExclamationCircleOutlined /> Indicators of Compromise (IoC)</>} className="section-card">
                <List
                  dataSource={threat.indicators_of_compromise}
                  renderItem={(indicator, index) => (
                    <List.Item key={index} className="ioc-item">
                      <div className="ioc-content">
                        <Text code className="ioc-text">{indicator}</Text>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => copyToClipboard(indicator, 'IoC')}
                          className="copy-ioc-btn"
                        />
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </motion.div>
          )}

          {/* Patch information */}
          {threat.patch_info && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card title={<><SecurityScanOutlined /> Fix Recommendations</>} className="section-card">
                <Alert
                  message="Fix Method"
                  description={threat.patch_info.fix_method}
                  type="warning"
                  showIcon
                  icon={<SecurityScanOutlined />}
                />
                {threat.patch_info.patch_url && (
                  <div style={{ marginTop: 16 }}>
                    <Button
                      type="primary"
                      icon={<LinkOutlined />}
                      onClick={() => openLink(threat.patch_info.patch_url)}
                    >
                      View Patch Details
                    </Button>
                  </div>
                )}
              </Card>
            </motion.div>
          )}
        </Col>

        {/* Right column - Sidebar information */}
        <Col xs={24} lg={8}>
          {/* Data sources */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card title={<><GlobalOutlined /> Data Sources</>} className="sidebar-card">
              <Timeline className="sources-timeline">
                {threat.credit?.sources?.map((source, index) => (
                  <Timeline.Item key={index} color="blue">
                    <div className="source-item">
                      <Text strong>{source.data_source}</Text>
                      <div className="source-meta">
                        <Text type="secondary">
                          Discoverer: {Array.isArray(source.discoverer) ? source.discoverer.join(', ') : source.discoverer}
                        </Text>
                        <Text type="secondary">
                          Date: {dayjs(source.discovery_date).format('YYYY-MM-DD')}
                        </Text>
                      </div>
                      {source.source_link && (
                        <Button
                          type="link"
                          size="small"
                          icon={<LinkOutlined />}
                          onClick={() => openLink(source.source_link)}
                        >
                          View Source
                        </Button>
                      )}
                    </div>
                  </Timeline.Item>
                )) || (
                  <Timeline.Item color="gray">
                    <Text type="secondary">No data source information available</Text>
                  </Timeline.Item>
                )}
              </Timeline>
            </Card>
          </motion.div>

          {/* Reference links */}
          {threat.references && threat.references.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card title={<><LinkOutlined /> Reference Links</>} className="sidebar-card">
                <List
                  dataSource={threat.references}
                  renderItem={(ref, index) => (
                    <List.Item key={index} className="reference-item">
                      <div className="reference-content">
                        <Tag color="blue" className="reference-type">
                          {ref.type}
                        </Tag>
                        <Button
                          type="link"
                          size="small"
                          icon={<EyeOutlined />}
                          onClick={() => openLink(ref.url)}
                          className="reference-link"
                        >
                          View Details
                        </Button>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </motion.div>
          )}

          {/* Repository links */}
          {threat.repository_url && threat.repository_url.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card title={<><GlobalOutlined /> Related Repositories</>} className="sidebar-card">
                <List
                  dataSource={threat.repository_url}
                  renderItem={(url, index) => (
                    <List.Item key={index} className="repo-item">
                      <Button
                        type="link"
                        size="small"
                        icon={<LinkOutlined />}
                        onClick={() => openLink(url)}
                        className="repo-link"
                        block
                      >
                        {url.length > 35 ? `${url.substring(0, 35)}...` : url}
                      </Button>
                    </List.Item>
                  )}
                />
              </Card>
            </motion.div>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default ThreatDetail