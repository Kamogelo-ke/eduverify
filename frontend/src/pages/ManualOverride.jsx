import React from 'react';
import { UserX, CheckCircle, XCircle, Camera, AlertTriangle, ShieldAlert } from 'lucide-react';

import InvigilatorHeader from '../components/InvigilatorHeader';
import Footer from '../components/Footer';
import { useManualOverride } from '../hooks/useManualOverride';
import '../styles/pages/_manualOverride.scss';

const ManualOverride = () => {
    // Destructure everything from our new hook
    const {
        deniedStudents,
        selectedStudent,
        isCapturing,
        evidenceImage,
        videoRef,
        handleSelectStudent,
        startInvestigation,
        captureAndGrant,
        denyPermanently
    } = useManualOverride();

    return (
        <div className="dashboard-wrapper">
            <InvigilatorHeader />

            <div className="override-container">
                {/* LEFT PANEL: Queue */}
                <div className="denied-list-panel">
                    <div className="panel-header">
                        <UserX size={20} />
                        <h3>Access Denied Queue</h3>
                        <span className="badge">{deniedStudents.length}</span>
                    </div>

                    <div className="student-list">
                        {deniedStudents.length === 0 ? (
                            <div className="empty-state">
                                <CheckCircle size={32} color="#10b981" style={{ marginBottom: '10px' }} />
                                <p>Queue is empty.</p>
                                <small>No students currently require overrides.</small>
                            </div>
                        ) : (
                            deniedStudents.map(student => (
                                <div
                                    key={student.id}
                                    className={`student-item ${selectedStudent?.id === student.id ? 'active' : ''}`}
                                    onClick={() => handleSelectStudent(student)}
                                >
                                    <div className="student-name">{student.name}</div>
                                    <div className="student-meta">
                                        <span>{student.id}</span>
                                        <span>{student.time}</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* RIGHT PANEL: Investigation */}
                <div className="action-panel">
                    {!selectedStudent ? (
                        <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '100px' }}>
                            <ShieldAlert size={64} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                            <h2>Select a student</h2>
                            <p>Select a student from the queue to investigate and override their access.</p>
                        </div>
                    ) : (
                        <>
                            <div className="action-header">
                                <h2>{selectedStudent.name} ({selectedStudent.id})</h2>
                                <p>System Flag: <strong>{selectedStudent.reason}</strong> at {selectedStudent.time}</p>
                            </div>

                            <div className="investigation-box">
                                {/* Camera Box */}
                                <div className="camera-feed">
                                    {!isCapturing && !evidenceImage && (
                                        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                                            <img
                                                src={selectedStudent.registeredImage}
                                                alt="Registered Profile"
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                            />
                                            {/* A nice little label at the bottom so they know what they are looking at */}
                                            <div style={{
                                                position: 'absolute',
                                                bottom: '15px',
                                                left: '50%',
                                                transform: 'translateX(-50%)',
                                                backgroundColor: 'rgba(0, 51, 102, 0.85)', // TUT Dark Blue transparent
                                                color: 'white',
                                                padding: '6px 16px',
                                                borderRadius: '20px',
                                                fontSize: '0.85rem',
                                                fontWeight: '600',
                                                backdropFilter: 'blur(4px)'
                                            }}>
                                                Registered Face
                                            </div>
                                        </div>
                                    )}

                                    {isCapturing && !evidenceImage && (
                                        <video ref={videoRef} autoPlay playsInline muted />
                                    )}

                                    {evidenceImage && (
                                        <img src={evidenceImage} alt="Evidence" />
                                    )}
                                </div>

                                {/* Buttons */}
                                <div className="action-buttons">
                                    <button className="btn-deny" onClick={denyPermanently}>
                                        <XCircle size={18} /> Deny Access
                                    </button>

                                    {!isCapturing ? (
                                        <button className="btn-grant" onClick={startInvestigation}>
                                            <Camera size={18} />  Override
                                        </button>
                                    ) : (
                                        <button className="btn-capture" onClick={captureAndGrant}>
                                            <CheckCircle size={18} /> Capture Face & Grant Access
                                        </button>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>

            <Footer />
        </div>
    );
};

export default ManualOverride;