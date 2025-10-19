import React, { useState, useEffect } from 'react';
import { Card, Select, Spin, message } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { motion } from 'framer-motion';

const { Option } = Select;

const ThreatTrendsChart = () => {
  const [loading, setLoading] = useState(true);
  const [trendsData, setTrendsData] = useState([]);
  const [packageManager, setPackageManager] = useState('all');
  const [totalThreats, setTotalThreats] = useState(0);

  const fetchTrends = async (pm) => {
    setLoading(true);
    try {
      const params = pm && pm !== 'all' ? { package_manager: pm } : {};
      const response = await axios.get('/api/threats/trends', { params });
      
      console.log('API Response:', response.data);
      
      if (response.data && response.data.trends) {
        setTrendsData(response.data.trends);
        setTotalThreats(response.data.total_threats || 0);
      } else {
        setTrendsData([]);
        setTotalThreats(0);
      }
    } catch (error) {
      console.error('Failed to fetch threat trends:', error);
      message.error('Failed to fetch trend data');
      setTrendsData([]);
      setTotalThreats(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends(packageManager);
  }, [packageManager]);

  const handlePackageManagerChange = (value) => {
    setPackageManager(value);
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          padding: '12px',
          border: '1px solid #e8e8e8',
          borderRadius: '6px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: 0, fontWeight: 'bold', color: '#1890ff' }}>
            {payload[0].payload.date}
          </p>
          <p style={{ margin: '4px 0 0 0', color: '#666' }}>
            Threats: <span style={{ fontWeight: 'bold', color: '#ff4d4f' }}>{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        maxWidth: '1800px',
        margin: '0 auto'
      }}
      className="trends-container"
    >
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '18px', fontWeight: '600', color: '#2d3748' }}>
              Threat Discovery Trends (Since 2020)
            </span>
            <Select
              value={packageManager}
              onChange={handlePackageManagerChange}
              style={{ width: 150 }}
              size="middle"
            >
              <Option value="all">All</Option>
              <Option value="pypi">PyPI</Option>
              <Option value="npm">NPM</Option>
            </Select>
          </div>
        }
        bordered={false}
        style={{
          borderRadius: '20px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          border: 'none',
          transition: 'all 0.3s ease'
        }}
        headStyle={{
          borderBottom: '2px solid #f0f2f5',
          borderRadius: '20px 20px 0 0',
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          padding: '0 32px',
          minHeight: '60px'
        }}
        bodyStyle={{
          padding: '28px 32px',
        }}
        className="trends-card"
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin size="large" />
          </div>
        ) : trendsData.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
            No data available
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '16px', textAlign: 'right', color: '#666' }}>
              Total Threats: <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff4d4f' }}>
                {totalThreats.toLocaleString()}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={trendsData}
                margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tick={{ fontSize: 11 }}
                  interval={0}
                  tickFormatter={(value, index) => {
                    // Only show January and July labels for each year
                    const parts = value.split('-');
                    if (parts[1] === '01' || parts[1] === '07') {
                      return value;
                    }
                    return '';
                  }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Threat Count', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  formatter={() => 'Monthly Threat Count'}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#1890ff"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#1890ff' }}
                  activeDot={{ r: 6, fill: '#ff4d4f' }}
                  name="Threat Count"
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        )}
      </Card>
    </motion.div>
  );
};

export default ThreatTrendsChart;

