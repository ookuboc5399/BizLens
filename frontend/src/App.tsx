import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/layout';
import Home from './pages/Home';
import CompanySearch from './pages/CompanySearch';
import CompanyDetail from './pages/CompanyDetail';
import CompanyComparison from './pages/CompanyComparison';
import EarningsCalendar from './pages/EarningsCalendar';
import FinancialReports from './pages/FinancialReports';
import FinancialReportDetail from './pages/FinancialReportDetail';
import { AdminRoute } from './components/AdminRoute';
import DataCollection from './pages/admin/DataCollection';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/company-search" element={<CompanySearch />} />
          <Route path="/company/:companyId" element={<CompanyDetail />} />
          <Route path="/company-comparison" element={<CompanyComparison />} />
          <Route path="/earnings-calendar" element={<EarningsCalendar />} />
          <Route path="/financial-reports" element={<FinancialReports />} />
          <Route path="/financial-reports/:companyId" element={<FinancialReportDetail />} />
          <Route
            path="/admin/data-collection"
            element={
              <AdminRoute>
                <DataCollection />
              </AdminRoute>
            }
          />
          <Route path="*" element={<Home />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
