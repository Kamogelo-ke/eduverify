import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import RegisterFace from './pages/RegisterFace';
import AdminDashboard from './pages/AdminDashboard';
import AddVenue from './pages/AddVenue';
import ManageVenues from './pages/ManageVenues';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AdminDashboard />} />
        <Route path="/students" element={<StudentManagement />} />
        <Route path="/register-face" element={<RegisterFace />} />
        <Route path="/admin-dashboard" element={<AdminDashboard />} />
        <Route path="/add-venue" element={<AddVenue />} />
        <Route path="/manage-venues" element={<ManageVenues />} /> 
      </Routes>
    </Router>
  );
}

export default App; 