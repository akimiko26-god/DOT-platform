import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Leads from './pages/Leads'
import Customers from './pages/Customers'
import CatalogManage from './pages/CatalogManage'
import CompanySettings from './pages/CompanySettings'
import QrTools from './pages/QrTools'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Employees from './pages/Employees'
import AdminPanel from './pages/AdminPanel'
import Profile from './pages/Profile'
import CompanyHub from './pages/CompanyHub'
import PublicCompany from './pages/PublicCompany'
import PublicCatalog from './pages/PublicCatalog'
import PublicContact from './pages/PublicContact'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('dot_token')
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/c/:slug" element={<PublicCompany />} />
        <Route path="/c/:slug/catalog" element={<PublicCatalog />} />
        <Route path="/c/:slug/contact" element={<PublicContact />} />

        <Route
          path="/app"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
          <Route path="company" element={<CompanyHub />} />
          <Route path="leads" element={<Leads />} />
          <Route path="customers" element={<Customers />} />
          <Route path="catalog" element={<CatalogManage />} />
          <Route path="settings" element={<CompanySettings />} />
          <Route path="qr" element={<QrTools />} />
          <Route path="employees" element={<Employees />} />
          <Route path="admin" element={<AdminPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
