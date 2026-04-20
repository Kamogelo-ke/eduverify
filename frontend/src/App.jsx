import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import StudentScanner from './pages/StudentScanner';
// 1. Import the Login page
import Login from './pages/Login';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Navigate to="/scanner" replace />} />

          <Route path="/dashboard" element={<StudentManagement />} />
          <Route path="/scanner" element={<StudentScanner />} />
          {/* 2. Add the login route */}
          <Route path="/login" element={<Login />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;