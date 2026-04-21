import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import RegisterFace from './pages/RegisterFace';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AdminDashboard />} />
        <Route path="/students" element={<StudentManagement />} />
        <Route path="/register-face" element={<RegisterFace />} />
        <Route path="/admin-dashboard" element={<AdminDashboard />} />
      </Routes>
    </Router>
  );
}

export default App; 