import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import StudentScanner from './pages/StudentScanner';
import Login from './pages/Login';
import RegisterFace from './pages/RegisterFace';
import ManualOverride from './pages/ManualOverride';
import AdminDashboard from './pages/AdminDashboard';
import AddVenue from './pages/AddVenue';
import ManageVenues from './pages/ManageVenues';
import EntranceMonitor from './pages/EntranceMonitor';
import AddInvigilator from './pages/AddInvigilator';
import InvigilatorHeader from './components/InvigilatorHeader';


function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          {/* Automatically redirect the base URL to the scanner */}
          <Route path="/" element={<Navigate to="/scanner" replace />} />

          <Route path="/students" element={<StudentManagement />} />
          <Route path="/register-face" element={<RegisterFace />} />
          <Route path="/scanner" element={<StudentScanner />} />
          <Route path="/login" element={<Login />} />
          <Route path="/override" element={<ManualOverride />} />
          <Route path="/admin-dashboard" element={<AdminDashboard />} />
          <Route path="/add-venue" element={<AddVenue />} />
          <Route path="/manage-venues" element={<ManageVenues />} />
          <Route path="/EntranceMonitor" element={<EntranceMonitor />} />
          <Route path="/add-invigilator" element={<AddInvigilator />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;

