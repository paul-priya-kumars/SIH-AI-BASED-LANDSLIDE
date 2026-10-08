import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { HomePage } from './pages/HomePage';
import { RiskMapPage } from './pages/RiskMapPage';
import { RouteSafetyPage } from './pages/RouteSafetyPage';
import { ReportHazardPage } from './pages/ReportHazardPage';
import { ReportsHistoryPage } from './pages/ReportsHistoryPage';
import { AlertsPage } from './pages/AlertsPage';
import { NotFoundPage } from './pages/NotFoundPage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="risk-map" element={<RiskMapPage />} />
          <Route path="route" element={<RouteSafetyPage />} />
          <Route path="report" element={<ReportHazardPage />} />
          <Route path="reports" element={<ReportsHistoryPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
