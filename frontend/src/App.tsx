import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/layout';
import Home from './pages/Home';
import { ScreeningPage } from './pages/screening';
import CompanySearch from './pages/CompanySearch';
import ConditionSearch from './pages/ConditionSearch';
import CompanyComparison from './pages/CompanyComparison';
import FinancialReports from './pages/FinancialReports';
import EarningsCalendar from './pages/EarningsCalendar';
import CompanyDetail from './pages/CompanyDetail';
import DataCollectionPage from './pages/admin/DataCollection';
import AdminLogin from './pages/admin/Login';
import { AdminRoute } from './components/AdminRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="screening" element={<ScreeningPage />} />
          <Route path="company-search" element={<CompanySearch />} />
          <Route path="condition-search" element={<ConditionSearch />} />
          <Route path="company-comparison" element={<CompanyComparison />} />
          <Route path="financial-reports" element={<FinancialReports />} />
          <Route path="earnings-calendar" element={<EarningsCalendar />} />
          <Route path="company/:id" element={<CompanyDetail />} />
          <Route path="admin/login" element={<AdminLogin />} />
          <Route
            path="admin/data-collection"
            element={
              <AdminRoute>
                <DataCollectionPage />
              </AdminRoute>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
