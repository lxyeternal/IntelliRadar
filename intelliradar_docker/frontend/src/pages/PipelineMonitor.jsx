import React, { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Typography,
  Progress,
  Timeline,
  Spin,
  Empty,
  Modal,
  Descriptions,
  Steps
} from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FireOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  DatabaseOutlined,
  ReloadOutlined,
  EyeOutlined,
  BugOutlined,
  BarChartOutlined,
  LineChartOutlined,
  DeploymentUnitOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import {
  getTaskDashboardSummary,
  getLatestPipelineTasks,
  getRunningPipelineTasks,
  getPipelineTaskDetail
} from '../services/api'
import './PipelineMonitor.css'

const { Title, Text } = Typography

const stageStatusBadge = {
  wait: { color: 'default', text: 'Pending' },
  process: { color: 'processing', text: 'In Progress' },
  finish: { color: 'success', text: 'Completed' },
  error: { color: 'error', text: 'Error' }
}

const formatNumber = (value) =>
  new Intl.NumberFormat('en-US').format(Number.isFinite(value) ? value : 0)

const PipelineMonitor = () => {
  const [dashboardData, setDashboardData] = useState(null)
  const [latestTasks, setLatestTasks] = useState([])
  const [runningTasks, setRunningTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [activeStage, setActiveStage] = useState(0)
  const [stagePinned, setStagePinned] = useState(false)

  const pipelineStages = useMemo(
    () => [
      {
        key: 'crawl',
        title: 'Source Discovery',
        description:
          'Collect fresh intelligence leads from every configured source',
        icon: <BugOutlined />
      },
      {
        key: 'analysis',
        title: 'Content Analysis',
        description:
          'LLM-driven extraction verifies indicators and attack context',
        icon: <ThunderboltOutlined />
      },
      {
        key: 'merge',
        title: 'Intelligence Merge',
        description:
          'Deduplicate, score confidence, and consolidate threat packages',
        icon: <DatabaseOutlined />
      },
      {
        key: 'publish',
        title: 'Publish & Monitor',
        description:
          'Persist to the database and watch the pipeline health over time',
        icon: <RocketOutlined />
      }
    ],
    []
  )

  useEffect(() => {
    fetchDashboardData()
    fetchLatestTasks()
    fetchRunningTasks()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchRunningTasks()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (runningTasks.length > 0) {
      fetchDashboardData()
      fetchLatestTasks()
    }
  }, [runningTasks.length])

  const referenceTask = useMemo(
    () => runningTasks[0] || latestTasks[0] || null,
    [runningTasks, latestTasks]
  )

  const stageStatusMap = useMemo(() => {
    const base = { crawl: 'wait', analysis: 'wait', merge: 'wait', publish: 'wait' }
    const task = referenceTask
    if (!task) {
      return base
    }

    const status = { ...base }

    if (task.status === 'failed') {
      status.crawl = task.source_results?.length ? 'finish' : 'error'
      status.analysis = 'error'
      status.merge = 'error'
      status.publish = 'error'
      return status
    }

    const sourceResults = task.source_results || []

    if (task.status === 'running') {
      status.crawl = 'process'
    }

    if (sourceResults.length > 0) {
      status.crawl = 'finish'
      status.analysis = task.status === 'running' ? 'process' : 'finish'
    }

    if (task.merger_result) {
      status.analysis = 'finish'
      status.merge =
        task.merger_result.status === 'failed'
          ? 'error'
          : task.merger_result.status === 'success'
          ? 'finish'
          : 'process'
    } else if (task.status === 'running' && sourceResults.length > 0) {
      status.merge = 'process'
    }

    if (task.status === 'completed') {
      status.merge = status.merge === 'error' ? 'error' : 'finish'
      status.publish = 'finish'
    } else if (
      task.status === 'running' &&
      (status.merge === 'finish' || task.merger_result)
    ) {
      status.publish = 'process'
    }

    return status
  }, [referenceTask])

  const currentStageIndex = useMemo(() => {
    const processIdx = pipelineStages.findIndex(
      (stage) => stageStatusMap[stage.key] === 'process'
    )
    if (processIdx >= 0) return processIdx

    const errorIdx = pipelineStages.findIndex(
      (stage) => stageStatusMap[stage.key] === 'error'
    )
    if (errorIdx >= 0) return errorIdx

    let lastFinished = -1
    pipelineStages.forEach((stage, idx) => {
      if (stageStatusMap[stage.key] === 'finish') {
        lastFinished = idx
      }
    })
    if (lastFinished >= 0) {
      return Math.min(lastFinished + 1, pipelineStages.length - 1)
    }
    return 0
  }, [pipelineStages, stageStatusMap])

  useEffect(() => {
    if (!stagePinned && activeStage !== currentStageIndex) {
      setActiveStage(currentStageIndex)
    }
  }, [currentStageIndex, stagePinned]) // eslint-disable-line react-hooks/exhaustive-deps

  const aggregatedSourceStats = useMemo(() => {
    const sourceResults = referenceTask?.source_results || []
    return sourceResults.reduce(
      (acc, item) => {
        acc.links += item.links_discovered || 0
        acc.content += item.content_saved || 0
        acc.failed += item.links_failed || 0
        return acc
      },
      { links: 0, content: 0, failed: 0 }
    )
  }, [referenceTask])

  const flowMetrics = useMemo(() => {
    const totalSources = referenceTask?.total_sources || 0
    const successSources = referenceTask?.success_sources || 0
    const successRate = totalSources
      ? Math.round((successSources / totalSources) * 100)
      : 0

    return [
      {
        key: 'sources',
        label: 'Sources processed',
        value: `${successSources}/${totalSources}`,
        hint: 'Completed / Total',
        progress: successRate,
        icon: <BugOutlined />
      },
      {
        key: 'links',
        label: 'Links discovered',
        value: formatNumber(aggregatedSourceStats.links),
        hint: 'Aggregated across crawlers',
        icon: <LineChartOutlined />
      },
      {
        key: 'content',
        label: 'Content saved',
        value: formatNumber(aggregatedSourceStats.content),
        hint: 'Articles ready for analysis',
        icon: <FileTextOutlined />
      },
      {
        key: 'intelligence',
        label: 'Merged intelligence',
        value: formatNumber(referenceTask?.merger_result?.merged_count ?? 0),
        hint: referenceTask?.merger_result
          ? 'Latest merge output'
          : 'Waiting for merge stage',
        icon: <DatabaseOutlined />
      }
    ]
  }, [referenceTask, aggregatedSourceStats])

  const fetchDashboardData = async () => {
    try {
      const response = await getTaskDashboardSummary()
      setDashboardData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchLatestTasks = async () => {
    try {
      const response = await getLatestPipelineTasks(10)
      setLatestTasks(response.data)
    } catch (error) {
      console.error('Failed to fetch latest tasks:', error)
    }
  }

  const fetchRunningTasks = async () => {
    try {
      const response = await getRunningPipelineTasks()
      setRunningTasks(response.data)
    } catch (error) {
      console.error('Failed to fetch running tasks:', error)
    }
  }

  const showTaskDetail = async (taskId) => {
    try {
      const response = await getPipelineTaskDetail(taskId)
      setSelectedTask(response.data)
      setDetailModalVisible(true)
    } catch (error) {
      console.error('Failed to fetch task detail:', error)
    }
  }

  const getStatusTag = (status) => {
    const config = {
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: 'COMPLETED' },
      running: { color: 'processing', icon: <PlayCircleOutlined />, text: 'RUNNING' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: 'FAILED' }
    }
    const conf =
      config[status] || { color: 'default', icon: null, text: status?.toUpperCase() }
    return (
      <Tag color={conf.color} icon={conf.icon}>
        {conf.text}
      </Tag>
    )
  }

  const getTaskTypeTag = (type) => {
    const config = {
      scheduled: { color: 'blue', text: 'SCHEDULED' },
      manual: { color: 'purple', text: 'MANUAL' },
      full: { color: 'cyan', text: 'FULL' }
    }
    const conf = config[type] || { color: 'default', text: type?.toUpperCase() }
    return <Tag color={conf.color}>{conf.text}</Tag>
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}m ${secs}s`
  }

  const formatDateTime = (datetime) => {
    if (!datetime) return 'N/A'
    const date = new Date(datetime)
    if (Number.isNaN(date.getTime())) return 'N/A'
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const activeStageKey = pipelineStages[activeStage]?.key
  const activeStageStatus = activeStageKey ? stageStatusMap[activeStageKey] : 'wait'
  const stageStatusMeta = stageStatusBadge[activeStageStatus] || stageStatusBadge.wait

  const renderStageDetail = () => {
    const stage = pipelineStages[activeStage]
    if (!stage) {
      return (
        <Empty
          className="stage-empty"
          description="Select a stage to explore its execution history"
        />
      )
    }

    if (!referenceTask && stage.key !== 'publish') {
      return (
        <Empty
          className="stage-empty"
          description="No pipeline execution data yet. Run a crawl to populate the dashboard."
        />
      )
    }

    switch (stage.key) {
      case 'crawl': {
        const sourceResults = referenceTask?.source_results || []
        if (!sourceResults.length) {
          return (
            <Empty
              className="stage-empty"
              description="Waiting for crawler output. Sources will appear as soon as the crawl starts."
            />
          )
        }

        return (
          <Timeline mode="left" className="stage-timeline">
            {sourceResults.map((result, index) => {
              const color =
                result.status === 'success'
                  ? '#52c41a'
                  : result.status === 'running'
                  ? '#1890ff'
                  : '#ff4d4f'
              return (
                <Timeline.Item
                  key={`${result.source}-${index}`}
                  color={color}
                >
                  <div className="timeline-item-header">
                    <Tag color="geekblue">{result.source}</Tag>
                    <Text strong>{formatNumber(result.links_discovered || 0)} links</Text>
                  </div>
                  <div className="timeline-item-meta">
                    <span>
                      <FileTextOutlined /> {formatNumber(result.content_saved || 0)} saved
                    </span>
                    <span>
                      <ClockCircleOutlined />{' '}
                      {result.duration ? `${result.duration.toFixed(1)}s` : 'N/A'}
                    </span>
                  </div>
                  {result.pipeline_mode === false && (
                    <Text type="secondary">Links-only mode</Text>
                  )}
                  {result.error && <Text type="danger">Error: {result.error}</Text>}
                </Timeline.Item>
              )
            })}
          </Timeline>
        )
      }
      case 'analysis': {
        const totalSources = referenceTask?.total_sources || 0
        const successSources = referenceTask?.success_sources || 0
        const failedSources = referenceTask?.failed_sources || 0
        const runningCount = Math.max(totalSources - successSources - failedSources, 0)
        const successRate = totalSources
          ? Math.round((successSources / totalSources) * 100)
          : 0

        return (
          <>
            <div className="stage-analysis-progress">
              <div className="progress-header">
                <Text strong>Source success rate</Text>
                <Text type="secondary">
                  {successSources}/{totalSources} sources completed
                </Text>
              </div>
              <Progress
                percent={successRate}
                status={failedSources > 0 ? 'exception' : 'active'}
                strokeColor="#667eea"
              />
              <Space size="small" wrap>
                <Tag color="success">Success {successSources}</Tag>
                <Tag color="processing">Running {runningCount}</Tag>
                <Tag color="error">Failed {failedSources}</Tag>
              </Space>
            </div>
            <div className="stage-analysis-grid">
              <div className="stage-analysis-card">
                <span className="analysis-label">Links collected</span>
                <span className="analysis-value">
                  {formatNumber(aggregatedSourceStats.links)}
                </span>
                <span className="analysis-footnote">
                  Across all active sources
                </span>
              </div>
              <div className="stage-analysis-card">
                <span className="analysis-label">Content saved</span>
                <span className="analysis-value">
                  {formatNumber(aggregatedSourceStats.content)}
                </span>
                <span className="analysis-footnote">
                  Ready for LLM verification
                </span>
              </div>
              <div className="stage-analysis-card">
                <span className="analysis-label">Failures</span>
                <span className="analysis-value">
                  {formatNumber(aggregatedSourceStats.failed)}
                </span>
                <span className="analysis-footnote">
                  Links requiring retry
                </span>
              </div>
            </div>
          </>
        )
      }
      case 'merge': {
        const merger = referenceTask?.merger_result
        if (!merger) {
          return (
            <Empty
              className="stage-empty"
              description="Merge stage will start after analysis completes."
            />
          )
        }

        const confidenceStats = merger.confidence_stats || {}
        return (
          <div className="stage-merge-content">
            <Row gutter={16} className="stage-merge-grid">
              <Col xs={24} md={12}>
                <div className="stage-analysis-card">
                  <span className="analysis-label">Packages merged</span>
                  <span className="analysis-value">
                    {formatNumber(merger.merged_count || 0)}
                  </span>
                  <span className="analysis-footnote">
                    Latest aggregation result
                  </span>
                </div>
              </Col>
              <Col xs={24} md={12}>
                <div className="stage-analysis-card">
                  <span className="analysis-label">Merge status</span>
                  <span className="analysis-value">
                    {(merger.status || 'pending').toUpperCase()}
                  </span>
                  <span className="analysis-footnote">
                    {merger.timestamp ? formatDateTime(merger.timestamp) : 'Awaiting completion'}
                  </span>
                </div>
              </Col>
            </Row>
            <Space size="small" wrap style={{ marginTop: 16 }}>
              <Tag color="success">High: {confidenceStats.high || 0}</Tag>
              <Tag color="warning">Medium: {confidenceStats.medium || 0}</Tag>
              <Tag color="error">Low: {confidenceStats.low || 0}</Tag>
            </Space>
            {merger.error && (
              <Text type="danger" style={{ marginTop: 12, display: 'block' }}>
                Error: {merger.error}
              </Text>
            )}
          </div>
        )
      }
      case 'publish': {
        const history = latestTasks.slice(0, 6)
        if (!history.length) {
          return (
            <Empty
              className="stage-empty"
              description="No recent pipeline executions yet."
            />
          )
        }

        return (
          <Timeline mode="left" className="stage-timeline">
            {history.map((task) => {
              const color =
                task.status === 'completed'
                  ? '#52c41a'
                  : task.status === 'running'
                  ? '#1890ff'
                  : '#ff4d4f'
              return (
                <Timeline.Item color={color} key={task.task_id}>
                  <div className="timeline-item-header">
                    {getStatusTag(task.status)}
                    <Text strong className="timeline-task-id">
                      {task.task_id.slice(0, 20)}...
                    </Text>
                  </div>
                  <div className="timeline-task-meta">
                    <span>
                      <ClockCircleOutlined /> {formatDateTime(task.start_time)}
                    </span>
                    <span>
                      <ThunderboltOutlined />{' '}
                      {formatNumber(task.merger_result?.merged_count || 0)} packages
                    </span>
                  </div>
                  <div className="timeline-task-actions">
                    <Button
                      type="link"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => showTaskDetail(task.task_id)}
                    >
                      View detail
                    </Button>
                  </div>
                </Timeline.Item>
              )
            })}
          </Timeline>
        )
      }
      default:
        return (
          <Empty
            className="stage-empty"
            description="Select a stage to explore its execution history"
          />
        )
    }
  }

  const taskColumns = [
    {
      title: 'Task ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      render: (id) => (
        <Text code copyable style={{ fontSize: '12px' }}>
          {id.slice(0, 25)}...
        </Text>
      )
    },
    {
      title: 'Type',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      align: 'center',
      render: (type) => getTaskTypeTag(type)
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      align: 'center',
      render: (status) => getStatusTag(status)
    },
    {
      title: 'Sources',
      key: 'sources',
      width: 120,
      align: 'center',
      render: (record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ color: '#52c41a' }}>
            {record.success_sources || 0}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            / {record.total_sources || 0}
          </Text>
        </Space>
      )
    },
    {
      title: 'Intelligence',
      key: 'intelligence',
      width: 100,
      align: 'center',
      render: (record) => (
        <Text strong style={{ color: '#1890ff' }}>
          {record.merger_result?.merged_count || 0}
        </Text>
      )
    },
    {
      title: 'Duration',
      dataIndex: 'total_duration',
      key: 'duration',
      width: 100,
      align: 'center',
      render: (duration) => <Text>{formatDuration(duration)}</Text>
    },
    {
      title: 'Start Time',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 160,
      render: (time) => <Text type="secondary">{formatDateTime(time)}</Text>
    },
    {
      title: 'Action',
      key: 'action',
      width: 100,
      align: 'center',
      render: (record) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => showTaskDetail(record.task_id)}
        >
          Detail
        </Button>
      )
    }
  ]

  if (loading) {
    return (
      <div className="pipeline-monitor-loading">
        <Spin size="large" />
        <Text style={{ marginTop: 16, color: 'white' }}>Loading Pipeline Data...</Text>
      </div>
    )
  }

  return (
    <div className="pipeline-monitor">
      <div className="monitor-hero">
        <div className="monitor-hero-content">
          <Title level={1} className="monitor-hero-title">
            <RocketOutlined /> Pipeline Monitor
          </Title>
          <Text className="monitor-hero-description">
            Visualize the IntelliRadar collection pipeline in real time. Track every stage—from crawling to intelligence merge—in one intuitive flow.
          </Text>
        </div>
      </div>

      {runningTasks.length > 0 && (
        <div className="running-tasks-alert">
          <Card className="running-alert-card">
            <Space size="large" align="center" wrap>
              <PlayCircleOutlined spin style={{ fontSize: 32, color: '#1890ff' }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  {runningTasks.length} Task{runningTasks.length > 1 ? 's' : ''} Running
                </Title>
                <Text type="secondary">
                  Pipeline is actively collecting intelligence...
                </Text>
              </div>
              <Button type="primary" icon={<ReloadOutlined />} onClick={fetchDashboardData}>
                Refresh
              </Button>
            </Space>
          </Card>
        </div>
      )}

      <div className="dashboard-stats">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card className="stat-card today-card">
              <div className="stat-card-header">
                <FireOutlined className="stat-icon" />
                <Title level={4}>Today</Title>
              </div>
              <Row gutter={[8, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Tasks"
                    value={dashboardData?.today?.total_tasks || 0}
                    valueStyle={{ color: '#667eea', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Success Rate"
                    value={dashboardData?.today?.success_rate || 0}
                    suffix="%"
                    valueStyle={{ color: '#52c41a', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Intelligence"
                    value={dashboardData?.today?.total_intelligence || 0}
                    valueStyle={{ color: '#1890ff', fontSize: 24 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Sources"
                    value={dashboardData?.today?.success_sources || 0}
                    valueStyle={{ color: '#faad14', fontSize: 24 }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} md={8}>
            <Card className="stat-card yesterday-card">
              <div className="stat-card-header">
                <ClockCircleOutlined className="stat-icon" />
                <Title level={4}>Yesterday</Title>
              </div>
              <Row gutter={[8, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Tasks"
                    value={dashboardData?.yesterday?.total_tasks || 0}
                    valueStyle={{ color: '#667eea', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Success Rate"
                    value={dashboardData?.yesterday?.success_rate || 0}
                    suffix="%"
                    valueStyle={{ color: '#52c41a', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Intelligence"
                    value={dashboardData?.yesterday?.total_intelligence || 0}
                    valueStyle={{ color: '#1890ff', fontSize: 24 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Sources"
                    value={dashboardData?.yesterday?.success_sources || 0}
                    valueStyle={{ color: '#faad14', fontSize: 24 }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} md={8}>
            <Card className="stat-card week-card">
              <div className="stat-card-header">
                <BarChartOutlined className="stat-icon" />
                <Title level={4}>This Week</Title>
              </div>
              <Row gutter={[8, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Tasks"
                    value={dashboardData?.week?.total_tasks || 0}
                    valueStyle={{ color: '#667eea', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Success Rate"
                    value={dashboardData?.week?.success_rate || 0}
                    suffix="%"
                    valueStyle={{ color: '#52c41a', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Intelligence"
                    value={dashboardData?.week?.total_intelligence || 0}
                    valueStyle={{ color: '#1890ff', fontSize: 24 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Sources"
                    value={dashboardData?.week?.success_sources || 0}
                    valueStyle={{ color: '#faad14', fontSize: 24 }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </div>

      <div className="pipeline-flow-section">
        <Card className="pipeline-flow-card" bordered={false}>
          <div className="pipeline-flow-header">
            <Space size="large" align="center">
              <DeploymentUnitOutlined className="pipeline-flow-icon" />
              <div>
                <Title level={3} style={{ marginBottom: 4 }}>
                  Pipeline flow overview
                </Title>
                <Text type="secondary">
                  Follow the intelligence stream from data collection to publication.
                </Text>
              </div>
            </Space>
            <Space size="small" wrap>
              {referenceTask ? (
                <>
                  {getStatusTag(referenceTask.status)}
                  <Text type="secondary">
                    Task {referenceTask.task_id.slice(0, 16)}...
                  </Text>
                </>
              ) : (
                <Tag color="default">No recent tasks</Tag>
              )}
            </Space>
          </div>

          <Steps
            current={activeStage}
            className="pipeline-steps"
            onChange={(index) => {
              setActiveStage(index)
              setStagePinned(index !== currentStageIndex)
            }}
            items={pipelineStages.map((stage) => ({
              title: stage.title,
              description: stage.description,
              status: stageStatusMap[stage.key],
              icon: stage.icon
            }))}
          />

          <div className="flow-metric-grid">
            {flowMetrics.map((metric) => (
              <div key={metric.key} className="flow-metric-card">
                <div className="metric-icon">{metric.icon}</div>
                <div className="metric-body">
                  <span className="metric-label">{metric.label}</span>
                  <span className="metric-value">{metric.value}</span>
                  <span className="metric-hint">{metric.hint}</span>
                  {metric.progress !== undefined && (
                    <Progress
                      percent={metric.progress}
                      size="small"
                      strokeColor="#667eea"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="stage-detail-panel">
            <div className="stage-detail-header">
              <div>
                <Title level={4} className="stage-detail-title">
                  {pipelineStages[activeStage]?.title}
                </Title>
                <Text type="secondary">
                  {pipelineStages[activeStage]?.description}
                </Text>
              </div>
              <div className="stage-detail-actions">
                {stageStatusMeta && (
                  <Tag color={stageStatusMeta.color}>{stageStatusMeta.text}</Tag>
                )}
                {stagePinned && (
                  <Button type="link" size="small" onClick={() => setStagePinned(false)}>
                    Follow live
                  </Button>
                )}
                {referenceTask && (
                  <Button
                    type="link"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => showTaskDetail(referenceTask.task_id)}
                  >
                    Current task
                  </Button>
                )}
              </div>
            </div>
            {renderStageDetail()}
          </div>
        </Card>
      </div>

      <div className="monitor-content">
        <Card
          title={
            <Space>
              <DatabaseOutlined />
              <span>Recent pipeline tasks</span>
            </Space>
          }
          className="tasks-card"
        >
          <Table
            dataSource={latestTasks}
            columns={taskColumns}
            rowKey="task_id"
            pagination={
              latestTasks.length > 5 ? {
                pageSize: 5,
                showSizeChanger: false,
                showTotal: (total) => `Total ${total} tasks`
              } : false
            }
            size="small"
            scroll={{ x: 1000 }}
          />
        </Card>
      </div>

      <Modal
        title={
          <Space>
            <DatabaseOutlined />
            <span>Task details</span>
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={1000}
        className="task-detail-modal"
      >
        {selectedTask && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Task ID" span={2}>
                <Text code copyable>{selectedTask.task_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Type">
                {getTaskTypeTag(selectedTask.task_type)}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                {getStatusTag(selectedTask.status)}
              </Descriptions.Item>
              <Descriptions.Item label="Start Time">
                {formatDateTime(selectedTask.start_time)}
              </Descriptions.Item>
              <Descriptions.Item label="End Time">
                {formatDateTime(selectedTask.end_time)}
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {formatDuration(selectedTask.total_duration)}
              </Descriptions.Item>
              <Descriptions.Item label="Workers">
                {selectedTask.workers}
              </Descriptions.Item>
            </Descriptions>

            <Title level={5} style={{ marginTop: 24 }}>
              Source execution results
            </Title>
            <Table
              dataSource={selectedTask.source_results}
              rowKey="source"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Source',
                  dataIndex: 'source',
                  key: 'source',
                  render: (source) => <Tag color="blue">{source}</Tag>
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  key: 'status',
                  render: (status) => getStatusTag(status)
                },
                {
                  title: 'Links Discovered',
                  dataIndex: 'links_discovered',
                  key: 'links_discovered',
                  align: 'center'
                },
                {
                  title: 'Content Saved',
                  dataIndex: 'content_saved',
                  key: 'content_saved',
                  align: 'center'
                },
                {
                  title: 'Failed',
                  dataIndex: 'links_failed',
                  key: 'links_failed',
                  align: 'center',
                  render: (failed) => (
                    <Text type={failed > 0 ? 'danger' : 'secondary'}>{failed}</Text>
                  )
                },
                {
                  title: 'Duration',
                  dataIndex: 'duration',
                  key: 'duration',
                  align: 'center',
                  render: (dur) => `${Number.isFinite(dur) ? dur.toFixed(1) : '0.0'}s`
                }
              ]}
            />

            {selectedTask.merger_result && (
              <>
                <Title level={5} style={{ marginTop: 24 }}>
                  Intelligence merger result
                </Title>
                <Card size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Statistic
                      title="Total intelligence packages merged"
                      value={selectedTask.merger_result.merged_count}
                      prefix={<ThunderboltOutlined />}
                    />
                    {selectedTask.merger_result.confidence_stats && (
                      <div>
                        <Text strong>Confidence distribution:</Text>
                        <Row gutter={16} style={{ marginTop: 8 }}>
                          <Col span={8}>
                            <Tag color="success">
                              HIGH: {selectedTask.merger_result.confidence_stats.high || 0}
                            </Tag>
                          </Col>
                          <Col span={8}>
                            <Tag color="warning">
                              MEDIUM: {selectedTask.merger_result.confidence_stats.medium || 0}
                            </Tag>
                          </Col>
                          <Col span={8}>
                            <Tag color="error">
                              LOW: {selectedTask.merger_result.confidence_stats.low || 0}
                            </Tag>
                          </Col>
                        </Row>
                      </div>
                    )}
                  </Space>
                </Card>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default PipelineMonitor
