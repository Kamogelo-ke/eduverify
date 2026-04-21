import React from 'react';
import { UserCheck, ShieldCheck, LayoutDashboard } from 'lucide-react';
import tutLogo from '../images/tut-logo.png';
import { useNavigate, useLocation } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();

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
        <button 
          className={location.pathname === '/' ? 'active' : ''} 
          onClick={() => navigate('/')}
        >
          <LayoutDashboard size={18} /> Dashboard
        </button>

        <button 
          className={location.pathname === '/students' ? 'active' : ''} 
          onClick={() => navigate('/students')}
        >
          <UserCheck size={18} /> Students
        </button>

        <button 
          className={location.pathname === '/register-face' ? 'active' : ''} 
          onClick={() => navigate('/register-face')}
        >
          <ShieldCheck size={18} /> Register Face
        </button>
      </div>
    </nav>
  );
};

export default Header;