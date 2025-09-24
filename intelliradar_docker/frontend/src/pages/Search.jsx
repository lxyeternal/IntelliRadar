import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from 'react-query'
import {
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  Table,
  Tag,
  Alert,
  Spin,
  Empty,
  Row,
  Col,
  Typography,
  Divider,
  Badge,
  Tooltip
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  BugOutlined,
  DatabaseOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import { searchThreats } from '../services/api'
import './Search.css'

const { Title, Paragraph, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

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
  high: { color: '#52c41a', label: 'High' },
  medium: { color: '#faad14', label: 'Medium' },
  low: { color: '#ff4d4f', label: 'Low' }
}

// Common attack methods
const COMMON_ATTACK_METHODS = [
  'Cache poisoning',
  'Cryptocurrency mining',
  'Data exfiltration',
  'Code injection',
  'Supply chain attack',
  'Typosquatting',
  'Malicious code execution',
  'Remote code execution',
  'Privilege escalation',
  'Information disclosure'
]

const Search = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [searchResults, setSearchResults] = useState([])
  const [hasSearched, setHasSearched] = useState(false)

  // Search mutation
  const searchMutation = useMutation(searchThreats, {
    onSuccess: (data) => {
      setSearchResults(data)
      setHasSearched(true)
    },
    onError: (error) => {
      console.error('Search failed:', error)
      setSearchResults([])
      setHasSearched(true)
    }
  })

  // Execute search
  const handleSearch = useCallback((values) => {
    const searchQuery = {
      query: values.query?.trim() || undefined,
      package_manager: values.package_manager,
      confidence_level: values.confidence_level,
      attack_methods: values.attack_methods,
      date_from: values.date_range?.[0]?.toISOString(),
      date_to: values.date_range?.[1]?.toISOString()
    }

    // Filter out empty values
    const filteredQuery = Object.fromEntries(
      Object.entries(searchQuery).filter(([_, value]) => 
        value !== undefined && value !== null && value !== ''
      )
    )

    searchMutation.mutate(filteredQuery)
  }, [searchMutation])

  // Reset form
  const handleReset = useCallback(() => {
    form.resetFields()
    setSearchResults([])
    setHasSearched(false)
  }, [form])

  // View details
  const viewDetail = useCallback((threatId) => {
    navigate(`/threats/${threatId}`)
  }, [navigate])

  // Table column definitions
  const columns = [
    {
      title: 'Package Name',
      dataIndex: 'package_name',
      key: 'package_name',
      width: 200,
      render: (text, record) => (
        <div className="search-package-cell">
          <div className="package-name">{text}</div>
          <div className="package-id">{record.threat_id}</div>
        </div>
      )
    },
    {
      title: 'Package Manager',
      dataIndex: 'package_manager',
      key: 'package_manager',
      width: 120,
      render: (manager) => {
        const config = PACKAGE_MANAGERS[manager] || { color: '#666', label: manager }
        return (
          <Tag color={config.color} className="package-manager-tag">
            {config.label}
          </Tag>
        )
      }
    },
    {
      title: 'Confidence',
      dataIndex: ['metadata', 'confidence_level'],
      key: 'confidence_level',
      width: 100,
      render: (level) => {
        const config = CONFIDENCE_LEVELS[level] || { color: '#666', label: level }
        return (
          <Badge
            color={config.color}
            text={config.label}
            className="confidence-badge"
          />
        )
      }
    },
    {
      title: 'Attack Methods',
      dataIndex: ['threat_info', 'attack_methods'],
      key: 'attack_methods',
      width: 300,
      render: (methods) => (
        <div className="search-attack-methods">
          {methods?.slice(0, 3).map((method, index) => (
            <Tag key={index} className="attack-method-tag" title={method}>
              {method.length > 20 ? `${method.substring(0, 20)}...` : method}
            </Tag>
          ))}
          {methods?.length > 3 && (
            <Tooltip title={methods.slice(3).join(', ')}>
              <Tag className="more-tag">+{methods.length - 3}</Tag>
            </Tooltip>
          )}
        </div>
      )
    },
    {
      title: 'Last Updated',
      dataIndex: ['metadata', 'last_updated'],
      key: 'last_updated',
      width: 150,
      render: (date) => (
        <div className="update-time">
          <ClockCircleOutlined className="time-icon" />
          {dayjs(date).format('YYYY-MM-DD')}
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
          <Tooltip title="View Details">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => viewDetail(record.threat_id)}
            className="search-action-btn"
          />
        </Tooltip>
      )
    }
  ]

  return (
    <div className="search-page">
      {/* Page title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="search-page-header"
      >
        <div className="search-header-content">
          <Title level={1} className="search-page-title">
            <SearchOutlined className="search-title-icon" />
            Advanced Search
          </Title>
          <Paragraph className="search-page-description">
            Search threat intelligence data precisely through multi-dimensional conditions, quickly locate security threat information you care about
          </Paragraph>
        </div>
      </motion.div>

      {/* Search form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="search-form-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSearch}
            className="search-form"
          >
            <Row gutter={[24, 16]}>
              {/* Keyword search */}
              <Col xs={24} lg={12}>
                <Form.Item
                  name="query"
                  label={
                    <span className="form-label">
                      <SearchOutlined /> Keyword Search
                    </span>
                  }
                >
                  <Input
                    placeholder="Search package names, attack methods, IoC indicators, etc..."
                    size="large"
                    className="search-input"
                  />
                </Form.Item>
              </Col>

              {/* Package manager */}
              <Col xs={24} sm={12} lg={6}>
                <Form.Item
                  name="package_manager"
                  label={
                    <span className="form-label">
                      <DatabaseOutlined /> Package Manager
                    </span>
                  }
                >
                  <Select
                    placeholder="Select Package Manager"
                    size="large"
                    allowClear
                    className="search-select"
                  >
                    {Object.entries(PACKAGE_MANAGERS).map(([key, config]) => (
                      <Option key={key} value={key}>
                        <Tag color={config.color} size="small">
                          {config.label}
                        </Tag>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>

              {/* Confidence level */}
              <Col xs={24} sm={12} lg={6}>
                <Form.Item
                  name="confidence_level"
                  label={
                    <span className="form-label">
                      <BugOutlined /> Confidence
                    </span>
                  }
                >
                  <Select
                    placeholder="Select Confidence"
                    size="large"
                    allowClear
                    className="search-select"
                  >
                    {Object.entries(CONFIDENCE_LEVELS).map(([key, config]) => (
                      <Option key={key} value={key}>
                        <Badge color={config.color} text={config.label} />
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>

              {/* Attack methods */}
              <Col xs={24} lg={12}>
                <Form.Item
                  name="attack_methods"
                  label={
                    <span className="form-label">
                      <FilterOutlined /> Attack Methods
                    </span>
                  }
                >
                  <Select
                    mode="multiple"
                    placeholder="Select Attack Methods"
                    size="large"
                    allowClear
                    className="search-select"
                    maxTagCount={2}
                  >
                    {COMMON_ATTACK_METHODS.map((method) => (
                      <Option key={method} value={method}>
                        {method}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>

              {/* Time range */}
              <Col xs={24} lg={12}>
                <Form.Item
                  name="date_range"
                  label={
                    <span className="form-label">
                      <ClockCircleOutlined /> Time Range
                    </span>
                  }
                >
                  <RangePicker
                    size="large"
                    placeholder={['Start Date', 'End Date']}
                    className="search-date-picker"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            {/* Search buttons */}
            <div className="search-actions">
              <Space size="middle">
                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  icon={<SearchOutlined />}
                  loading={searchMutation.isLoading}
                  className="search-submit-btn"
                >
                  Search Threats
                </Button>
                <Button
                  size="large"
                  icon={<ClearOutlined />}
                  onClick={handleReset}
                  className="search-reset-btn"
                >
                  Reset Conditions
                </Button>
              </Space>
            </div>
          </Form>
        </Card>
      </motion.div>

      {/* Search results */}
      {hasSearched && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="search-results-card">
            <div className="search-results-header">
              <Title level={3} className="results-title">
                Search Results
                {searchResults.length > 0 && (
                  <Text className="results-count">
                    (Found {searchResults.length} records)
                  </Text>
                )}
              </Title>
            </div>

            {searchMutation.isError && (
              <Alert
                message="Search Failed"
                description="An error occurred during the search. Please check your search criteria or try again later."
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Spin spinning={searchMutation.isLoading} tip="Searching...">
              {searchResults.length > 0 ? (
                <Table
                  columns={columns}
                  dataSource={searchResults}
                  rowKey="threat_id"
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} records`
                  }}
                  className="search-results-table"
                  rowClassName="search-result-row"
                />
              ) : (
                !searchMutation.isLoading && (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <div>
                        <Text>No threat data matching the criteria found</Text>
                        <br />
                        <Text type="secondary">
                          Try adjusting search criteria or using broader keywords
                        </Text>
                      </div>
                    }
                    className="search-empty"
                  />
                )
              )}
            </Spin>
          </Card>
        </motion.div>
      )}

      {/* Search tips */}
      {!hasSearched && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="search-tips-card">
            <Title level={4} className="tips-title">
              Search Tips
            </Title>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <div className="tip-item">
                  <Text strong>🔍 Keyword Search</Text>
                  <Paragraph>
                    Supports searching for package names, attack methods, IoC indicators and other keywords. Use spaces to separate multiple keywords
                  </Paragraph>
                </div>
              </Col>
              <Col xs={24} md={12}>
                <div className="tip-item">
                  <Text strong>🎯 Precise Filtering</Text>
                  <Paragraph>
                    Filter precisely by package manager, confidence level, attack methods and other criteria to improve search accuracy
                  </Paragraph>
                </div>
              </Col>
              <Col xs={24} md={12}>
                <div className="tip-item">
                  <Text strong>📅 Time Range</Text>
                  <Paragraph>
                    Select a specific time range to find threat intelligence discovered within a certain period
                  </Paragraph>
                </div>
              </Col>
              <Col xs={24} md={12}>
                <div className="tip-item">
                  <Text strong>🔄 Combined Search</Text>
                  <Paragraph>
                    Multiple conditions can be combined, and the system will automatically perform AND logic search
                  </Paragraph>
                </div>
              </Col>
            </Row>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

export default Search
