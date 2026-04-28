import React from 'react';
import { Activity, ShieldAlert, LogOut } from 'lucide-react';
import tutLogo from '../images/tut-logo.png';
import { useNavigate, useLocation } from 'react-router-dom';

const InvigilatorHeader = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.clear(); // optional
    navigate('/login');
  };

  return (
    <nav className="main-nav">
      
      {/* BRAND */}
      <div className="brand">
        <img src={tutLogo} alt="TUT Logo" />
        <div className="text">
          <h1>Tshwane University of Technology</h1>
          <p>Invigilator Portal</p>
          <span className="motto">"We empower people"</span>
        </div>
      </div>

      {/* NAV ACTIONS */}
      <div className="nav-actions">

        {/* Entrance Monitor (FIRST PAGE) */}
        <button
          className={location.pathname === '/entrance-monitor' ? 'active' : ''}
          onClick={() => navigate('/EntranceMonitor')}
        >
          <Activity size={18} /> Entrance Monitor
        </button>

        {/* Override */}
        <button
          className={location.pathname === '/override' ? 'active' : ''}
          onClick={() => navigate('/override')}
        >
          <ShieldAlert size={18} /> Override
        </button>

        {/* Logout */}
        <button className="logout-btn" onClick={handleLogout}>
          <LogOut size={18} style={{ marginRight: "6px" }} />
          Logout
        </button>

      </div>
    </nav>
  );
};

export default InvigilatorHeader;