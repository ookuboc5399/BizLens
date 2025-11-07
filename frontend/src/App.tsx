import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/layout';
import Home from './pages/Home';
import CompanySearch from './pages/CompanySearch';
import CompanyDetail from './pages/CompanyDetail';
import CompanyAnalysis from './pages/CompanyAnalysis';
import CompanyComparison from './pages/CompanyComparison';
import EarningsCalendar from './pages/EarningsCalendar';
import FinancialReports from './pages/FinancialReports';
import FinancialReportDetail from './pages/FinancialReportDetail';
import AuthCallback from './pages/AuthCallback';
import { AdminRoute } from './components/AdminRoute';
import { ProtectedRoute } from './components/ProtectedRoute';
import Login from './pages/Login';
import AdminLogin from './pages/admin/Login';
import DataCollection from './pages/admin/DataCollection';
import { SupabaseClient } from '@supabase/supabase-js';

interface AppProps {
  supabase: SupabaseClient;
}

function App({ supabase }: AppProps) {
  return (
    <Router>
      <Layout>
        <Routes>
          {/* 一般ユーザー向けログインページ */}
          <Route path="/login" element={<Login supabase={supabase} />} />
          {/* 管理者向けログインページ */}
          <Route path="/admin/login" element={<AdminLogin supabase={supabase} />} />

          {/* 保護されたルート */}
          <Route
            path="/"
            element={
              <ProtectedRoute supabase={supabase}>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/company-search"
            element={
              <ProtectedRoute supabase={supabase}>
                <CompanySearch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/company/:companyId"
            element={
              <ProtectedRoute supabase={supabase}>
                <CompanyDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/company-analysis/:companyId"
            element={
              <ProtectedRoute supabase={supabase}>
                <CompanyAnalysis />
              </ProtectedRoute>
            }
          />
          <Route
            path="/company-comparison"
            element={
              <ProtectedRoute supabase={supabase}>
                <CompanyComparison />
              </ProtectedRoute>
            }
          />
          <Route
            path="/earnings-calendar"
            element={
              <ProtectedRoute supabase={supabase}>
                <EarningsCalendar />
              </ProtectedRoute>
            }
          />
          <Route
            path="/financial-reports"
            element={<FinancialReports />}
          />
          <Route
            path="/auth/callback"
            element={<AuthCallback />}
          />
          <Route
            path="/financial-reports/:companyId"
            element={
              <ProtectedRoute supabase={supabase}>
                <FinancialReportDetail supabase={supabase} />
              </ProtectedRoute>
            }
          />
          {/* 管理者専用ルート */}
          <Route
            path="/admin"
            element={
              <AdminRoute supabase={supabase}>
                <DataCollection />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/data-collection"
            element={
              <AdminRoute supabase={supabase}>
                <DataCollection />
              </AdminRoute>
            }
          />
          {/* 存在しないパスはホームにリダイレクト（保護されたルート経由） */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;