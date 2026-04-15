import React, { useState, useRef, useEffect } from 'react';
import { Camera, UserCheck, CameraOff, Scan, CheckCircle, Loader2, AlertCircle } from 'lucide-react';

import Header from '../components/Header';
import Footer from '../components/Footer';
import { useStudentScanner } from '../hooks/useStudentScanner'; // Your perfectly named hook!

import '../styles/pages/studentScanner.scss';

const StudentScanner = () => {
    // Bring in the verify function and loading state from your hook
    const { verifyStudentFace, isVerifying } = useStudentScanner();

    // Application State
    const [isScanning, setIsScanning] = useState(false);
    const [selectedExam, setSelectedExam] = useState('');
    const [capturedImage, setCapturedImage] = useState(null);
    const [verificationResult, setVerificationResult] = useState(null); // 'success' or 'failed'

    // HTML Element References
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);

    // Cleanup camera when leaving the page
    useEffect(() => {
        return () => stopCamera();
    }, []);

    // --- Voice Helper Function ---
    const speakMessage = (text) => {
        // Cancel any currently playing speech so they don't overlap
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    };

    const startCamera = async () => {
        if (!selectedExam) {
            alert("Please select an exam before starting the camera.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setIsScanning(true);

            // Reset previous results when starting a new scan
            setCapturedImage(null);
            setVerificationResult(null);
        } catch (err) {
            console.error("Error accessing webcam: ", err);
            alert("Could not access the webcam. Please grant permission in your browser.");
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setIsScanning(false);
    };

    const toggleScanner = () => {
        if (isScanning) {
            stopCamera();
        } else {
            startCamera();
        }
    };

    const captureAndVerify = async () => {
        if (videoRef.current && canvasRef.current) {
            const video = videoRef.current;
            const canvas = canvasRef.current;

            // 1. Capture the frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // 2. Get Image Data and update UI
            const imageUrl = canvas.toDataURL('image/jpeg');
            setCapturedImage(imageUrl);
            stopCamera();

            // 3. Send to Backend
            try {
                const response = await verifyStudentFace(selectedExam, imageUrl);

                // 4. Handle Response and trigger Voice
                if (response && response.success) {
                    setVerificationResult('success');
                    speakMessage("Access Granted. Student verified.");
                } else {
                    setVerificationResult('failed');
                    speakMessage("Access Denied. Identity not recognized.");
                }
            } catch (error) {
                console.error("Verification error:", error);
                setVerificationResult('failed');
                speakMessage("Verification failed. Please try again.");
            }
        }
    };

    return (
        <div className="dashboard-wrapper">
            <Header />

            <div className="scanner-page-container">
                {/* LEFT PANEL */}
                <div className="panel camera-panel">
                    <div className="panel-header">
                        <Camera size={20} />
                        Face Recognition Camera
                    </div>

                    <div className="panel-content">
                        <div className="form-group">
                            <label>Select Exam</label>
                            <select
                                value={selectedExam}
                                onChange={(e) => setSelectedExam(e.target.value)}
                                disabled={isScanning || isVerifying}
                            >
                                <option value="" disabled>Choose an exam...</option>
                                <option value="cs101">Computer Science 101</option>
                                <option value="se202">Software Engineering 202</option>
                            </select>
                        </div>

                        <div className="camera-display">
                            <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>

                            <video
                                ref={videoRef}
                                autoPlay
                                playsInline
                                className="video-stream"
                                style={{ display: isScanning ? 'block' : 'none' }}
                            ></video>

                            {!isScanning && (
                                <div className="camera-off-state">
                                    <CameraOff size={48} className="large-icon" />
                                    <h3>Camera is off</h3>
                                    <p>Click "Start Scanning" to begin</p>
                                </div>
                            )}
                        </div>

                        {isScanning ? (
                            <button className="scan-button capture-btn" onClick={captureAndVerify} disabled={isVerifying}>
                                <Scan size={20} />
                                {isVerifying ? 'Verifying...' : 'Capture & Verify'}
                            </button>
                        ) : (
                            <button className="scan-button" onClick={toggleScanner} disabled={isVerifying}>
                                <Camera size={20} />
                                Start Scanning
                            </button>
                        )}
                    </div>
                </div>

                {/* RIGHT PANEL */}
                <div className="panel results-panel">
                    <div className="panel-header">
                        <UserCheck size={20} />
                        Verification Results
                    </div>

                    <div className="panel-content empty-results">
                        {/* STATE 1: Empty (Waiting to scan) */}
                        {!capturedImage && !isVerifying && (
                            <div className="empty-state">
                                <Scan size={64} className="scan-frame" />
                                <h3>No verification performed yet</h3>
                                <p>Start scanning to verify student identity</p>
                            </div>
                        )}

                        {/* STATE 2: Processing (Waiting for backend) */}
                        {isVerifying && (
                            <div className="success-state">
                                <img src={capturedImage} alt="Captured" className="captured-preview" style={{ opacity: 0.5 }} />
                                <div className="status-badge" style={{ backgroundColor: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1' }}>
                                    <Loader2 size={16} className="animate-spin" />
                                    Verifying with Database...
                                </div>
                            </div>
                        )}

                        {/* STATE 3: Finished (Backend replied) */}
                        {capturedImage && !isVerifying && verificationResult && (
                            <div className="success-state">
                                <img src={capturedImage} alt="Captured" className="captured-preview" />

                                {verificationResult === 'success' ? (
                                    <div className="status-badge success">
                                        <CheckCircle size={16} />
                                        Identity Verified Successfully
                                    </div>
                                ) : (
                                    <div className="status-badge" style={{ backgroundColor: '#fef2f2', color: '#b91c1c', border: '1px solid #f87171' }}>
                                        <AlertCircle size={16} />
                                        Verification Failed - No Match
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <Footer />
        </div>
    );
};

export default StudentScanner;