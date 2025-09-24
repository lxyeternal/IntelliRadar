import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import {
  Card,
  Table,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Tooltip,
  Pagination,
  Row,
  Col,
  Statistic,
  Alert,
  Spin,
  Empty,
  Badge
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import { fetchThreats } from '../services/api'
import './ThreatDatabase.css'

const { Search } = Input
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

const ThreatDatabase = () => {
  const navigate = useNavigate()
  
  // State management
  const [filters, setFilters] = useState({
    search: '',
    package_manager: undefined,
    confidence_level: undefined
  })
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20
  })
  const [sorting, setSorting] = useState({
    sort_by: 'metadata.last_updated',
    sort_order: 'desc'
  })

  // Get threat data
  const {
    data: threatData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['threats', filters, pagination, sorting],
    () => fetchThreats({
      ...filters,
      ...pagination,
      ...sorting
    }),
    {
      keepPreviousData: true,
      refetchInterval: 60000 // Refresh every 1 minute
    }
  )

  // Handle search
  const handleSearch = useCallback((value) => {
    setFilters(prev => ({ ...prev, search: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }, [])

  // Handle filtering
  const handleFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }, [])

  // Handle pagination
  const handlePageChange = useCallback((page, pageSize) => {
    setPagination({ page, page_size: pageSize })
  }, [])

  // Handle sorting
  const handleTableChange = useCallback((pagination, filters, sorter) => {
    if (sorter.field) {
      setSorting({
        sort_by: sorter.field,
        sort_order: sorter.order === 'ascend' ? 'asc' : 'desc'
      })
    }
  }, [])

  // View details
  const viewDetail = useCallback((record) => {
    // Use the correct ID field from the record
    const threatId = record.id || record._id || record.threat_id
    navigate(`/threats/${threatId}`)
  }, [navigate])

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters({
      search: '',
      package_manager: undefined,
      confidence_level: undefined
    })
    setPagination({ page: 1, page_size: 20 })
  }, [])

  // Table column definitions
  const columns = [
    {
      title: 'Package Name',
      dataIndex: 'package_name',
      key: 'package_name',
      width: 200,
      render: (text, record) => (
        <div className="package-cell">
          <div className="package-name">{text}</div>
          <div className="package-id">{record.id}</div>
        </div>
      ),
      sorter: true
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
      },
      filters: Object.entries(PACKAGE_MANAGERS).map(([key, value]) => ({
        text: value.label,
        value: key
      })),
      sorter: true
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
      },
      filters: Object.entries(CONFIDENCE_LEVELS).map(([key, value]) => ({
        text: value.label,
        value: key
      })),
      sorter: true
    },
    {
      title: 'Attack Methods',
      dataIndex: ['threat_info', 'attack_methods'],
      key: 'attack_methods',
      width: 250,
      render: (methods) => (
        <div className="attack-methods">
          {methods?.slice(0, 2).map((method, index) => (
            <Tag key={index} className="attack-method-tag">
              {method}
            </Tag>
          ))}
          {methods?.length > 2 && (
            <Tooltip title={methods.slice(2).join(', ')}>
              <Tag className="more-tag">+{methods.length - 2}</Tag>
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
      ),
      sorter: true,
      defaultSortOrder: 'descend'
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => viewDetail(record)}
              className="action-btn"
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  if (error) {
    return (
      <div className="threat-database">
        <Alert
          message="Data Loading Failed"
          description="Unable to retrieve threat intelligence data. Please check your network connection or try again later."
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="threat-database">
      {/* Page title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="page-header"
      >
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">
              <DatabaseOutlined className="title-icon" />
              Threat Intelligence Database
            </h1>
            <p className="page-description">
              Comprehensive collection of malicious component threat information from major package managers, updated in real-time to enhance security protection
            </p>
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
            className="refresh-btn"
          >
            Refresh Data
          </Button>
        </div>
      </motion.div>

      {/* Statistics overview */}
      {threatData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Row gutter={[16, 16]} className="stats-row">
            <Col xs={24} sm={8}>
              <Card className="stat-card">
                <Statistic
                  title="Total Threats"
                  value={threatData.total}
                  prefix={<ExclamationCircleOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card className="stat-card">
                <Statistic
                  title="Current Page"
                  value={`${threatData.page}/${threatData.total_pages}`}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card className="stat-card">
                <Statistic
                  title="Per Page"
                  value={threatData.page_size}
                  prefix={<FilterOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
          </Row>
        </motion.div>
      )}

      {/* Search and filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="filter-card">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} lg={8}>
              <Search
                placeholder="Search package names, attack methods..."
                allowClear
                enterButton={<SearchOutlined />}
                onSearch={handleSearch}
                className="search-input"
              />
            </Col>
            <Col xs={24} sm={6} lg={4}>
              <Select
                placeholder="Package Manager"
                allowClear
                value={filters.package_manager}
                onChange={(value) => handleFilter('package_manager', value)}
                className="filter-select"
              >
                {Object.entries(PACKAGE_MANAGERS).map(([key, config]) => (
                  <Option key={key} value={key}>
                    <Tag color={config.color} size="small">
                      {config.label}
                    </Tag>
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={6} lg={4}>
              <Select
                placeholder="Confidence"
                allowClear
                value={filters.confidence_level}
                onChange={(value) => handleFilter('confidence_level', value)}
                className="filter-select"
              >
                {Object.entries(CONFIDENCE_LEVELS).map(([key, config]) => (
                  <Option key={key} value={key}>
                    <Badge color={config.color} text={config.label} />
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Space className="filter-actions">
                <Button onClick={resetFilters}>
                  Reset
                </Button>
                <Button type="primary" onClick={() => refetch()}>
                  Apply Filter
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>
      </motion.div>

      {/* Data table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="table-card">
          <Spin spinning={isLoading} tip="Loading threat data...">
            <Table
              columns={columns}
              dataSource={threatData?.threats || []}
              rowKey={(record) => record.id || record._id}
              pagination={false}
              onChange={handleTableChange}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No threat data available"
                  />
                )
              }}
              className="threats-table"
              rowClassName="threat-row"
            />
          </Spin>

          {/* Pagination */}
          {threatData && threatData.total > 0 && (
            <div className="pagination-wrapper">
              <Pagination
                current={threatData.page}
                pageSize={threatData.page_size}
                total={threatData.total}
                onChange={handlePageChange}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) =>
                  `${range[0]}-${range[1]} of ${total} records`
                }
                className="threats-pagination"
              />
            </div>
          )}
        </Card>
      </motion.div>
    </div>
  )
}

export default ThreatDatabase
