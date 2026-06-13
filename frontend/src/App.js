import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate, useNavigate } from "react-router-dom";
import { Toaster } from "sonner";

import { AuthProvider, useAuth } from "@/auth";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import AuthCallback from "@/pages/AuthCallback";
import RoleSelect from "@/pages/RoleSelect";
import WorkerDashboard from "@/pages/WorkerDashboard";
import ClientDashboard from "@/pages/ClientDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import Roadmap from "@/pages/Roadmap";

const ProtectedRoute = ({ children, role }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-slate-900 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (!user.role) return <Navigate to="/select-role" replace />;
  if (role && user.role !== role && user.role !== "admin") {
    return <Navigate to={`/${user.role}`} replace />;
  }
  return children;
};

// Redirects /dashboard to the right dashboard for the user's role
const DashboardRedirect = () => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-slate-900 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (!user.role) return <Navigate to="/select-role" replace />;
  return <Navigate to={`/${user.role}`} replace />;
};

const AppRouter = () => {
  const location = useLocation();
  // Synchronous detection of session_id in URL fragment (prevents race conditions)
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/roadmap" element={<Roadmap />} />
      <Route path="/select-role" element={<RoleSelect />} />
      <Route path="/dashboard" element={<DashboardRedirect />} />
      <Route path="/worker" element={<ProtectedRoute role="worker"><WorkerDashboard /></ProtectedRoute>} />
      <Route path="/client" element={<ProtectedRoute role="client"><ClientDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster position="top-right" richColors closeButton />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
