import React from 'react';
import { UserCheck, ShieldCheck, LayoutDashboard, Settings } from 'lucide-react';
import tutLogo from '../images/tut-logo.png';

const Header = () => {
  return (
    <nav className="main-nav">
      <div className="brand">
        <img src={tutLogo} alt="TUT Logo" />
        <div className="text">
          <h1>Tshwane University of Technology</h1>
          <p>Exam Verification System</p>
          <span className="motto">"We empower people"</span>
        </div>
      </div>
      <div className="nav-actions">
        <button><UserCheck size={18} /> Verify Student</button>
        <button><ShieldCheck size={18} /> Register Face</button>
        <button><LayoutDashboard size={18} /> Dashboard</button>
        <button className="admin-pill"><Settings size={18} /> Admin</button>
      </div>
    </nav>
  );
};

export default Header;