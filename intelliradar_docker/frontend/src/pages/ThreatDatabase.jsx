import React, { useState, useEffect } from 'react'
import { 
  Table, 
  Card, 
  Input, 
  Select, 
  DatePicker, 
  Button, 
  Space, 
  Tag, 
  Typography,
  Row,
  Col,
  message,
  Tooltip
} from 'antd'
import { Link } from 'react-router-dom'
import { 
  SearchOutlined, 
  ReloadOutlined, 
  EyeOutlined,
  CalendarOutlined,
  FilterOutlined
} from '@ant-design/icons'
import { getThreats } from '../services/api'
import './ThreatDatabase.css'

const { Title } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

const ThreatDatabase = () => {
  const [threats, setThreats] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  
  // Search filter state
  const [filters, setFilters] = useState({
    package_name: '',
    package_manager: '',
    data_source: '',
    confidence_level: '',
    date_range: null,
  })

  const packageManagerOptions = [
    { value: 'pypi', label: 'PyPI', color: '#3776ab' },
    { value: 'npm', label: 'npm', color: '#cb3837' },
    { value: 'maven', label: 'Maven', color: '#f89820' },
    { value: 'nuget', label: 'NuGet', color: '#004880' },
    { value: 'gem', label: 'RubyGems', color: '#701516' },
    { value: 'go', label: 'Go', color: '#00add8' },
  ]

  const confidenceLevels = [
    { value: 'high', label: 'High', color: '#52c41a' },
    { value: 'medium', label: 'Medium', color: '#faad14' },
    { value: 'low', label: 'Low', color: '#ff4d4f' },
  ]

  const dataSourceOptions = [
    { value: 'snykdb', label: 'SnykDB' },
    { value: 'github', label: 'GitHub' },
    { value: 'sonatype', label: 'Sonatype' },
    { value: 'phylum', label: 'Phylum' },
    { value: 'thehackernews', label: 'The Hacker News' },
    { value: 'tuxcare', label: 'TuxCare' },
    { value: 'medium', label: 'Medium' },
    { value: 'checkpoint', label: 'Check Point' },
    { value: 'qianxin', label: 'Qianxin' },
    { value: 'fortinet', label: 'Fortinet' },
    { value: 'rhisac', label: 'RH-ISAC' },
    { value: 'checkmarx', label: 'Checkmarx' },
    { value: 'cybersecuritynews', label: 'Cybersecurity News' },
    { value: 'jfrog', label: 'JFrog' },
    { value: 'socket', label: 'Socket' },
    { value: 'snyk', label: 'Snyk' },
    { value: 'bleepingcomputer', label: 'BleepingComputer' },
    { value: 'reversinglabs', label: 'ReversingLabs' },
    { value: 'datadoghq', label: 'Datadog' },
    { value: 'securityaffairs', label: 'Security Affairs' },
    { value: 'securityweek', label: 'SecurityWeek' },
  ]

  // Fetch threat data
  const fetchThreats = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters,
      }

      // Handle date range
      if (filters.date_range && filters.date_range.length === 2) {
        params.date_from = filters.date_range[0].toISOString()
        params.date_to = filters.date_range[1].toISOString()
      }

      const response = await getThreats(params)
      setThreats(response.threats)
      setPagination({
        current: response.page,
        pageSize: response.page_size,
        total: response.total,
      })
    } catch (error) {
      console.error('Failed to fetch threats:', error)
      message.error('Failed to load threat data')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchThreats()
  }, [])

  // Handle search
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchThreats(1, pagination.pageSize)
  }

  // Reset search
  const handleReset = () => {
    const resetFilters = {
      package_name: '',
      package_manager: '',
      data_source: '',
      confidence_level: '',
      date_range: null,
    }
    setFilters(resetFilters)
    setPagination(prev => ({ ...prev, current: 1 }))
    
    // 立即使用重置的过滤器获取数据
    setLoading(true)
    setTimeout(async () => {
      try {
        const params = {
          page: 1,
          page_size: pagination.pageSize,
          // 不包含任何过滤条件，获取所有数据
        }

        const response = await getThreats(params)
        setThreats(response.threats)
        setPagination({
          current: response.page,
          pageSize: response.page_size,
          total: response.total,
        })
      } catch (error) {
        console.error('Failed to fetch threats after reset:', error)
        message.error('Failed to load threat data')
      } finally {
        setLoading(false)
      }
    }, 50)
  }

  // Handle pagination change
  const handleTableChange = (paginationInfo) => {
    fetchThreats(paginationInfo.current, paginationInfo.pageSize)
  }

  // Format version information
  const formatVersions = (versions) => {
    if (!versions) return 'N/A'
    if (typeof versions === 'string') return versions
    if (Array.isArray(versions)) {
      const displayVersions = versions.slice(0, 3)
      return displayVersions.join(', ') + (versions.length > 3 ? '...' : '')
    }
    return 'N/A'
  }

  // Format data source
  const formatDataSources = (credit) => {
    if (!credit?.sources) return 'N/A'
    const sources = credit.sources.map(s => s.data_source).filter(Boolean)
    const uniqueSources = [...new Set(sources)]
    return uniqueSources.slice(0, 2).join(', ') + (uniqueSources.length > 2 ? '...' : '')
  }

  // Table column definitions
  const columns = [
    {
      title: 'Package Name',
      dataIndex: 'package_name',
      key: 'package_name',
      width: 200,
      render: (text) => (
        <span style={{ fontWeight: 600, color: '#2d3748' }}>{text}</span>
      ),
    },
    {
      title: 'Package Manager',
      dataIndex: 'package_manager',
      key: 'package_manager',
      width: 150,
      render: (manager) => {
        const option = packageManagerOptions.find(opt => opt.value === manager)
        return (
          <Tag color={option?.color || 'default'}>
            {option?.label || manager}
          </Tag>
        )
      },
    },
    {
      title: 'Versions',
      dataIndex: 'package_versions',
      key: 'package_versions',
      width: 200,
      render: (versions) => (
        <Tooltip title={Array.isArray(versions) ? versions.join(', ') : versions}>
          <span style={{ color: '#64748b' }}>{formatVersions(versions)}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Confidence',
      dataIndex: ['metadata', 'confidence_level'],
      key: 'confidence_level',
      width: 120,
      render: (level) => {
        const conf = confidenceLevels.find(c => c.value === level)
        return (
          <Tag color={conf?.color || 'default'}>
            {conf?.label || level}
          </Tag>
        )
      },
    },
    {
      title: 'Data Sources',
      dataIndex: 'credit',
      key: 'data_sources',
      width: 150,
      render: (credit) => (
        <span style={{ color: '#64748b' }}>{formatDataSources(credit)}</span>
      ),
    },
    {
      title: 'Last Updated',
      dataIndex: ['metadata', 'last_updated'],
      key: 'last_updated',
      width: 150,
      render: (date) => (
        <span style={{ color: '#64748b' }}>
          {new Date(date).toLocaleDateString()}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Link to={`/threats/${record.id}`}>
          <Button type="primary" size="small" icon={<EyeOutlined />}>
            Details
          </Button>
        </Link>
      ),
    },
  ]

  return (
    <div className="threat-database">
      <div className="database-header">
        <Title level={2} style={{ color: 'white', textAlign: 'center', margin: '40px 0' }}>
          🛡️ IntelliRadar Database
        </Title>
      </div>

      <div className="database-content">
        <Card className="search-card">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Input
                placeholder="Search package name..."
                value={filters.package_name}
                onChange={(e) => setFilters({ ...filters, package_name: e.target.value })}
                prefix={<SearchOutlined />}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Select
                placeholder="Package Manager"
                value={filters.package_manager}
                onChange={(value) => setFilters({ ...filters, package_manager: value })}
                allowClear
                style={{ width: '100%' }}
              >
                {packageManagerOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    <Tag color={option.color} style={{ margin: 0 }}>
                      {option.label}
                    </Tag>
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Select
                placeholder="Data Source"
                value={filters.data_source}
                onChange={(value) => setFilters({ ...filters, data_source: value })}
                allowClear
                style={{ width: '100%' }}
              >
                {dataSourceOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Select
                placeholder="Confidence Level"
                value={filters.confidence_level}
                onChange={(value) => setFilters({ ...filters, confidence_level: value })}
                allowClear
                style={{ width: '100%' }}
              >
                {confidenceLevels.map(level => (
                  <Option key={level.value} value={level.value}>
                    <Tag color={level.color} style={{ margin: 0 }}>
                      {level.label}
                    </Tag>
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} md={12}>
              <RangePicker
                placeholder={['Start Date', 'End Date']}
                value={filters.date_range}
                onChange={(dates) => setFilters({ ...filters, date_range: dates })}
                style={{ width: '100%' }}
                prefix={<CalendarOutlined />}
              />
            </Col>
            <Col xs={24} md={12}>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button
                  type="primary"
                  icon={<FilterOutlined />}
                  onClick={handleSearch}
                  loading={loading}
                >
                  Search
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleReset}
                >
                  Reset
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        <Card className="table-card">
          <Table
            columns={columns}
            dataSource={threats}
            rowKey={(record) => record.id || record.mongo_id || record._id}
            loading={loading}
            pagination={{
              ...pagination,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} threats`,
            }}
            onChange={handleTableChange}
            scroll={{ x: 1200 }}
          />
        </Card>
      </div>
    </div>
  )
}

export default ThreatDatabase