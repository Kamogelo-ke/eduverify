// src/pages/AdminDashboard.jsx
import { FaUsers, FaCheckCircle, FaBook, FaChartLine, FaCalendarAlt, FaChartPie } from "react-icons/fa";
import React from 'react';
import '../styles/pages/AdminDashboard.scss';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAdminDashboard } from '../hooks/useAdminDashboard';

const AdminDashboard = () => {

  const { stats, recentVerifications, upcomingExams } = useAdminDashboard();

  return (
    <div className="admin-dashboard">
      <Header />

      {/* Stats Cards */}
     <div className="stats-cards">
  <div className="stat-card">
    <div className="card-top">
      <h4>Total Students</h4>
      <FaUsers className="icon" />
    </div>
    <p>{stats.totalStudents}</p>
  </div>

  <div className="stat-card">
    <div className="card-top">
      <h4>Face Registered</h4>
      <FaCheckCircle className="icon" />
    </div>
    <p>{stats.faceRegistered}</p>
  </div>

  <div className="stat-card">
    <div className="card-top">
      <h4>Total Exams</h4>
      <FaBook className="icon" />
    </div>
    <p>{stats.totalExams}</p>
  </div>

  <div className="stat-card">
    <div className="card-top">
      <h4>Active Exams</h4>
      <FaChartLine className="icon" />
    </div>
    <p>{stats.activeExams}</p>
  </div>

  <div className="stat-card">
    <div className="card-top">
      <h4>Today's Verifications</h4>
      <FaCalendarAlt className="icon" />
    </div>
    <p>{stats.todaysVerifications}</p>
  </div>

  <div className="stat-card">
    <div className="card-top">
      <h4>Success Rate</h4>
      <FaChartPie className="icon" />
    </div>
    <p>{stats.successRate}</p>
  </div>
</div>

      {/* Dashboard Bottom */}
      <div className="dashboard-bottom">

        {/* LEFT SIDE */}
        <div className="left-panel">
          <div className="section">
            <h3>Recent Verifications</h3>

            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Student</th>
                  <th>Exam</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Message</th>
                </tr>
              </thead>

              <tbody>
                {recentVerifications.map((item, index) => (
                  <tr key={index}>
                    <td>{item.time}</td>
                    <td>{item.student}</td>
                    <td>
                      <span className="badge">{item.exam}</span>
                    </td>
                    <td>
                      <span className="status-error">{item.status}</span>
                    </td>
                    <td>{item.confidence}</td>
                    <td>{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className="right-panel">
          <div className="section">
            <h3>Upcoming Exams</h3>

            {upcomingExams.map((exam, index) => (
              <div className="exam-card" key={index}>
                <div className="exam-header">
                  <span className="badge">{exam.code}</span>
                  <span>{exam.date} {exam.time}</span>
                </div>

                <h4>{exam.name}</h4>
                <p>{exam.faculty}</p>

                <p><strong>Venue:</strong> {exam.venue}</p>
                <p><strong>Duration:</strong> {exam.duration}</p>
              </div>
            ))}
          </div>
        </div>

      </div>

      <Footer />
    </div>
  );
};

export default AdminDashboard;