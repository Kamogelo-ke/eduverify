import React, { useState } from 'react';
import { Camera, Save, UserPlus, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Shared Components
import Header from '../components/Header';
import Footer from '../components/Footer';

// Hooks
import { useCamera } from '../hooks/useCamera';

// Styles
import '../styles/pages/RegisterFace.scss';

const RegisterFace = () => {
  const navigate = useNavigate();
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Logic Separation via Custom Hook
  const { videoRef, error } = useCamera(isCameraActive);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isCameraActive) return alert("Please start the camera and capture your face.");

    setIsSubmitting(true);

    // 1. Capture image from video stream
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const faceImage = canvas.toDataURL('image/jpeg');

    // 2. Gather form data
    const formData = new FormData(e.target);
    const studentData = {
      studentNumber: formData.get('studentNumber'),
      email: formData.get('email'),
      firstName: formData.get('firstName'),
      lastName: formData.get('lastName'),
      faculty: formData.get('faculty'),
      program: formData.get('program'),
      faceImage: faceImage // Base64 string for Prisma
    };

    // 3. API Call
    try {
      const response = await fetch('http://localhost:5000/api/students/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(studentData),
      });

      if (response.ok) {
        alert("Student Registered Successfully!");
        navigate('/dashboard');
      } else {
        const errData = await response.json();
        alert(`Registration failed: ${errData.message}`);
      }
    } catch (err) {
      console.error("API Error:", err);
      alert("Server connection failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="dashboard-wrapper">
      <Header />

      <main className="content-area">
        <div className="register-grid">
          
          {/* Left Column: Face Capture */}
          <section className="card">
            <div className="card-header">
              <Camera size={20} />
              <h2>Face Capture</h2>
            </div>
            <div className="card-content">
              <div className="camera-box">
                {!isCameraActive ? (
                  <div className="camera-placeholder">
                    <UserPlus size={48} className="user-plus-icon" />
                    <h3>Ready to capture face</h3>
                    <p>Click "Start Camera" to begin</p>
                  </div>
                ) : (
                  <div className="camera-feed">
                    <video 
                      ref={videoRef}
                      autoPlay 
                      playsInline 
                      muted
                      className="video-element"
                      style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }}
                    />
                    {error && <p className="error-text" style={{color: 'red'}}>Error: {error.message}</p>}
                  </div>
                )}
              </div>
              <button 
                type="button"
                className="btn-camera" 
                onClick={() => setIsCameraActive(true)}
                disabled={isCameraActive}
              >
                <Camera size={18} /> {isCameraActive ? "Camera Active" : "Start Camera"}
              </button>
            </div>
          </section>

          {/* Right Column: Student Registration */}
          <section className="card">
            <div className="card-header">
              <UserPlus size={20} />
              <h2>Student Registration</h2>
            </div>
            <div className="card-content">
              <form className="registration-form" onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Student Number *</label>
                    <input name="studentNumber" type="text" placeholder="e.g., 2023018456" required />
                  </div>
                  </div>


                <div className="info-box">
                  <AlertTriangle size={24} className="info-icon" />
                  <div>
                    <strong>Face Data Required</strong>
                    <p>Please capture your face using the camera</p>
                  </div>
                </div>

                <button type="submit" className="btn-submit" disabled={isSubmitting}>
                  <Save size={18} /> {isSubmitting ? "Processing..." : "Complete Registration"}
                </button>
              </form>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default RegisterFace;