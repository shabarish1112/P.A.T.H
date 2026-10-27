import { Navigate, Route, Routes, useLocation } from 'react-router-dom';

import { AsyncState } from './components/AsyncState';
import { Layout } from './components/Layout';
import { useAuth } from './contexts/AuthContext';
import Admin from './pages/Admin';
import Analytics from './pages/Analytics';
import Anomalies from './pages/Anomalies';
import Control from './pages/Control';
import Dashboard from './pages/Dashboard';
import Datasets from './pages/Datasets';
import Investigation from './pages/Investigation';
import Login from './pages/Login';
import PublicAnalysis from './pages/PublicAnalysis';
import ChangePassword from './pages/ChangePassword';
import Queue from './pages/Queue';
import Transactions from './pages/Transactions';

function ProtectedRoute() {
  const auth = useAuth();
  const location = useLocation();
  if (auth.loading) return <AsyncState loading />;
  if (!auth.authenticated)
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (auth.user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }
  if (auth.user?.role === 'member' && location.pathname !== '/change-password')
    return <Navigate to="/" replace />;
  return <Layout />;
}

function AdminRoute() {
  const auth = useAuth();
  if (auth.user?.role !== 'admin') return <Navigate to="/workspace" replace />;
  return <Admin />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicAnalysis />} />
      <Route path="/results/:analysisId" element={<PublicAnalysis />} />
      <Route path="/signup" element={<Login signup />} />
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="workspace" element={<Dashboard />} />
        <Route path="change-password" element={<ChangePassword />} />
        <Route path="datasets" element={<Datasets />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="control" element={<Control />} />
        <Route path="anomalies" element={<Anomalies />} />
        <Route path="investigation" element={<Investigation />} />
        <Route path="investigation/:transactionId" element={<Investigation />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="queue" element={<Queue />} />
        <Route path="admin" element={<AdminRoute />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
