import React from "react";
import { ShieldCheck, UserCheck, UserX, AlertTriangle, Activity, Clock } from 'lucide-react';
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useEntranceMonitor } from "../hooks/useEntranceMonitor";

// Styles
import "../styles/pages/EntranceMonitor.scss";

const EntranceMonitor = () => {
  const { scans, stats } = useEntranceMonitor();

  return (
    <div className="dashboard-wrapper">
      <Header />

      <main className="content-area">
        <div className="monitor-header">
          <h1>Live Entrance Monitor</h1>
          <p>Real-time student verification activity</p>
        </div>

        {/* HIGH-CONTRAST STAT CARDS */}
        <div className="stats-grid">
          <div className="stat-card total">
            <div className="stat-info">
              <span className="label">Total Scans</span>
              <span className="value">{stats.total}</span>
              <span className="subtext">Last 30 min</span>
            </div>
            <div className="stat-icon"><Activity size={24} /></div>
          </div>

          <div className="stat-card granted">
            <div className="stat-info">
              <span className="label">Granted</span>
              <span className="value">{stats.granted}</span>
            </div>
            <div className="stat-icon"><UserCheck size={24} /></div>
          </div>

          <div className="stat-card denied">
            <div className="stat-info">
              <span className="label">Denied</span>
              <span className="value">{stats.denied}</span>
            </div>
            <div className="stat-icon"><UserX size={24} /></div>
          </div>

          <div className="stat-card overrides">
            <div className="stat-info">
              <span className="label">Overrides</span>
              <span className="value">{stats.overrides}</span>
            </div>
            <div className="stat-icon"><AlertTriangle size={24} /></div>
          </div>
        </div>

        {/* RECENT SCANS LIST (Text Only) */}
        <section className="main-card">
          <header>
            <div className="title">
              <ShieldCheck size={20} /> 
              <h2>Recent Entrance Scans</h2>
            </div>
          </header>

          <div className="card-body">
            <div className="scans-list">
              {scans.map((scan) => (
                <div key={scan.id} className="scan-item">
                  <div className="student-profile">
                    <div className={`status-indicator ${scan.status.toLowerCase()}`}></div>
                    <div className="student-details">
                      <span className="name">{scan.name}</span>
                      <span className="number">{scan.studentNo}</span>
                    </div>
                  </div>
                  
                  <div className="scan-meta">
                    <span className={`status-pill ${scan.status.toLowerCase()}`}>
                      {scan.status}
                    </span>
                    <span className="time">
                      <Clock size={14} /> {scan.time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default EntranceMonitor;