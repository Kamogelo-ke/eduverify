import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StudentManagement from './pages/StudentManagement';
import RegisterFace from './pages/RegisterFace';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<StudentManagement />} />
        <Route path="/register-face" element={<RegisterFace />} />
      </Routes>
    </Router>
  );
}

export default App; 