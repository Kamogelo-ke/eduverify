import React from "react";
import { Settings, PlusCircle, Edit3, Trash2, Calendar, MapPin, Search, Users, X, Save } from 'lucide-react';
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useVenues } from "../hooks/useVenues";

// Styles
import "../styles/pages/ManageVenues.scss";

const ManageVenues = () => {
  const navigate = useNavigate();
  const {
    venues,
    editingVenue,
    deleteVenue,
    startEdit,
    handleEditChange,
    saveEdit,
    setEditingVenue
  } = useVenues();

  return (
    <div className="dashboard-wrapper">
      <Header />

      <main className="content-area">
        {/* Navigation Tabs */}
        <div className="tab-row">
          <button className="active">
            <Settings size={18} /> Manage Scheduled Exams
          </button>
          <button className="inactive" onClick={() => navigate('/add-venue')}>
            <PlusCircle size={18} /> Schedule New Exam
          </button>
        </div>

        {/* MAIN DATA CARD */}
        <section className="main-card">
          <header>
            <div className="title">
              <Calendar size={20} /> 
              <h2>Scheduled Examination Sessions</h2>
            </div>
          </header>

          <div className="card-body">
            <div className="table-container">
              <table className="venue-table">
                <thead>
                  <tr>
                    <th>Venue & Location</th>
                    <th>Module / Course</th>
                    <th>Date & Time</th>
                    <th>Invigilators</th>
                    <th className="text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {venues.map((venue) => (
                    <tr key={venue.id}>
                      <td>
                        <div className="info-cell">
                          <span className="primary-text">{venue.venueName}</span>
                          <span className="secondary-text"><MapPin size={12} /> {venue.location}</span>
                        </div>
                      </td>
                      <td>
                        <div className="info-cell">
                          <span className="primary-text">{venue.courseCode}</span>
                          <span className="secondary-text">{venue.moduleName}</span>
                        </div>
                      </td>
                      <td>
                        <div className="info-cell">
                          <span className="primary-text">{venue.date}</span>
                          <span className="secondary-text">{venue.time}</span>
                        </div>
                      </td>
                      <td>
                        <div className="invigilator-tags">
                          {venue.invigilators.map((inv, i) => (
                            <span key={i} className="tag">{inv}</span>
                          ))}
                        </div>
                      </td>
                      <td className="actions-cell">
                        <button className="btn-edit" onClick={() => startEdit(venue)}>
                          <Edit3 size={16} /> Edit
                        </button>
                        <button className="btn-delete" onClick={() => deleteVenue(venue.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>

      {/* ================= EDIT MODAL ================= */}
      {editingVenue && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">
                <Edit3 size={18} />
                <h3>Edit Exam Assignment</h3>
              </div>
              <button className="close-x" onClick={() => setEditingVenue(null)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              <div className="input-group">
                <label>Venue Name</label>
                <input 
                  type="text"
                  name="venueName" 
                  value={editingVenue.venueName} 
                  onChange={handleEditChange} 
                />
              </div>

              <div className="input-group">
                <label>Course Code</label>
                <input 
                  type="text"
                  name="courseCode" 
                  value={editingVenue.courseCode} 
                  onChange={handleEditChange} 
                />
              </div>

              <div className="row">
                <div className="input-group">
                  <label>Date</label>
                  <input 
                    type="date" 
                    name="date" 
                    value={editingVenue.date} 
                    onChange={handleEditChange} 
                  />
                </div>
                <div className="input-group">
                  <label>Time</label>
                  <input 
                    type="time" 
                    name="time" 
                    value={editingVenue.time} 
                    onChange={handleEditChange} 
                  />
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-cancel" onClick={() => setEditingVenue(null)}>
                Cancel
              </button>
              <button className="btn-save" onClick={saveEdit}>
                <Save size={16} /> Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default ManageVenues;