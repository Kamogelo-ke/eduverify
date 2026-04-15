import React from 'react';
import tutLogo from '../images/tut-logo.png';

const Footer = () => {
  return (
    <footer className="main-footer">
      <div className="footer-brand">
        <img src={tutLogo} alt="TUT Logo" />
        <div className="footer-text">
          <h3>Tshwane University of Technology</h3>
          <p>Exam Verification System v1.0</p>
        </div>
      </div>
      <div className="footer-right">
        <p>© 2026 TUT. All rights reserved.</p>
        <span className="motto">"We empower people"</span>
      </div>
    </footer>
  );
};

export default Footer;