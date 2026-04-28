import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import StudentScanner from './pages/StudentScanner';
import Login from './pages/Login';
import RegisterFace from './pages/RegisterFace';
import ManualOverride from './pages/ManualOverride';

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
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;