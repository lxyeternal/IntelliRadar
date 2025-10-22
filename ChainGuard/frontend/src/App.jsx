import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Navigation from './components/Navigation'
import HomePage from './pages/HomePage'
import ThreatDatabase from './pages/ThreatDatabase'
import ThreatDetail from './pages/ThreatDetail'
import Search from './pages/Search'
import Statistics from './pages/Statistics'
import PipelineMonitor from './pages/PipelineMonitor'
import AuthPage from './pages/Auth'
import './App.css'

const { Content } = Layout

function App() {
  return (
    <div className="App">
      <Router>
        <Layout className="app-layout">
          <Navigation />
          <Content className="app-content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/database" element={<ThreatDatabase />} />
              <Route path="/search" element={<Search />} />
              <Route path="/statistics" element={<Statistics />} />
              <Route path="/pipeline-monitor" element={<PipelineMonitor />} />
              <Route path="/threats/:id" element={<ThreatDetail />} />
              <Route path="/login" element={<AuthPage />} />
              <Route path="/register" element={<AuthPage />} />
            </Routes>
          </Content>
        </Layout>
      </Router>
    </div>
  )
}

export default App
