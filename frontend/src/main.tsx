import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { HomePage } from './pages/HomePage'
import { MissionsPage } from './pages/MissionsPage'
import { MissionDashboard } from './pages/MissionDashboard'
import { SatellitePage } from './pages/SatellitePage'
import { SonarPage } from './pages/SonarPage'
import { ReportPage } from './pages/ReportPage'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><Routes><Route element={<AppLayout />}><Route path="/" element={<HomePage />} /><Route path="/missions" element={<MissionsPage />} /><Route path="/missions/:id" element={<MissionDashboard />} /><Route path="/missions/:id/satellite" element={<SatellitePage />} /><Route path="/missions/:id/sonar" element={<SonarPage />} /><Route path="/missions/:id/risk" element={<MissionDashboard />} /><Route path="/missions/:id/report" element={<ReportPage />} /></Route></Routes></BrowserRouter></React.StrictMode>,
)
