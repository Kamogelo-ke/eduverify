import React from 'react';
import { useNavigate } from 'react-router-dom'; // 1. Import the hook
import { UserCheck, Lock } from 'lucide-react';
import tutLogo from '../images/tut-logo.png';

const Header2 = () => {
    const navigate = useNavigate(); // 2. Initialize the hook

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
                {/* 3. Add onClick to navigate to the scanner */}
                <button onClick={() => navigate('/scanner')}>
                    <UserCheck size={18} /> Scanner
                </button>

                {/* 4. Add onClick to navigate back to the dashboard */}
                <button onClick={() => navigate('/login')}>
                    <Lock size={18} /> Login
                </button>
            </div>
        </nav>
    );
};

export default Header2;