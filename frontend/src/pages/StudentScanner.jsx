import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, UserCheck, CameraOff, Scan, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import * as faceapi from 'face-api.js';

import Header2 from '../components/Header2';
import Footer from '../components/Footer';
import { useStudentScanner } from '../hooks/useStudentScanner';

import '../styles/pages/studentScanner.scss';

// Hardcode the exam ID
const PRESET_EXAM = "cs101";

const StudentScanner = () => {
    const { verifyStudentFace, isVerifying } = useStudentScanner();

    // Application State
    const [isScanning, setIsScanning] = useState(false);
    const [capturedImage, setCapturedImage] = useState(null);
    const [verificationResult, setVerificationResult] = useState(null);

    // NEW: Track if the AI models are ready
    const [modelsLoaded, setModelsLoaded] = useState(false);

    // HTML Element References
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);

    // 1. MOVED INSIDE: Load models when the component mounts
    useEffect(() => {
        const loadModels = async () => {
            try {
                const MODEL_URL = '/models'; // Ensure your models are inside public/models
                await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
                setModelsLoaded(true);
            } catch (error) {
                console.error("Failed to load FaceAPI models:", error);
            }
        };
        loadModels();

        // Cleanup camera when leaving the page
        return () => stopCamera();
    }, []);

    const speakMessage = (text) => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    };

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setIsScanning(true);
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

    // 2. MOVED INSIDE: Detect face with a stricter threshold
    const detectFace = async () => {
        if (!videoRef.current || !modelsLoaded) return false;

        try {
            const detections = await faceapi.detectAllFaces(
                videoRef.current,
                // INCREASED SCORE THRESHOLD: 0.6 means the AI must be 60% sure it's a face. 
                // If it still detects walls, change this to 0.7 or 0.8.
                new faceapi.TinyFaceDetectorOptions({ scoreThreshold: 0.6 })
            );

            return detections.length > 0;
        } catch (error) {
            console.error("Detection error:", error);
            return false;
        }
    };

    // Wrap capture logic in useCallback so it can be used in the auto-scan interval
    const captureAndVerify = useCallback(async () => {
        if (!videoRef.current || !canvasRef.current || isVerifying || verificationResult === 'success') {
            return;
        }

        // Check if face exists first
        const faceExists = await detectFace();

        if (!faceExists) {
            // No face → stay completely quiet
            setCapturedImage(null);
            setVerificationResult(null);
            return;
        }

        const video = videoRef.current;
        const canvas = canvasRef.current;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageUrl = canvas.toDataURL('image/jpeg');
        setCapturedImage(imageUrl);

        try {
            const response = await verifyStudentFace(PRESET_EXAM, imageUrl);

            if (response && response.success) {
                setVerificationResult('success');
                speakMessage("Access granted");

                setTimeout(() => {
                    setCapturedImage(null);
                    setVerificationResult(null);
                }, 5000);

            } else if (response && response.noFaceDetected) {
                setCapturedImage(null);
                setVerificationResult(null);

            } else {
                setVerificationResult('failed');
                speakMessage("Access denied");

                setTimeout(() => {
                    setVerificationResult(null);
                }, 2000);
            }
        } catch (error) {
            console.error("Verification error:", error);
            setCapturedImage(null);
            setVerificationResult(null);
        }
    }, [isVerifying, verifyStudentFace, verificationResult, modelsLoaded]);

    // Auto-Scan Loop: Trigger a scan every 3 seconds automatically
    useEffect(() => {
        let scanInterval;

        // Only run interval if camera is on, models are loaded, and not waiting on a success screen
        if (isScanning && modelsLoaded && !isVerifying && verificationResult !== 'success') {
            scanInterval = setInterval(() => {
                captureAndVerify();
            }, 3000);
        }

        return () => clearInterval(scanInterval);
    }, [isScanning, isVerifying, verificationResult, modelsLoaded, captureAndVerify]);

    return (
        <div className="dashboard-wrapper">
            <Header2 />

            <div className="scanner-page-container">
                {/* LEFT PANEL */}
                <div className="panel camera-panel">
                    <div className="panel-header">
                        <Camera size={20} />
                        Auto Face Recognition Camera
                    </div>

                    <div className="panel-content">
                        <div style={{ marginBottom: '1rem', color: '#64748b', fontSize: '0.875rem' }}>
                            <strong>Active Exam Session:</strong> Computer Science 101 ({PRESET_EXAM})
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
                                    <h3>System Offline</h3>
                                    <p>Click below to initialize auto-scanner</p>
                                </div>
                            )}
                        </div>

                        {/* Scanner Toggle Button */}
                        <button
                            className="scan-button"
                            onClick={toggleScanner}
                            style={{ backgroundColor: isScanning ? '#ef4444' : '#00529B' }}
                            // Disable the button until models finish downloading
                            disabled={!modelsLoaded}
                        >
                            <Camera size={20} />
                            {!modelsLoaded ? 'Loading AI Models...' : isScanning ? 'Stop Auto-Scanner' : 'Start Auto-Scanner'}
                        </button>
                    </div>
                </div>

                {/* RIGHT PANEL */}
                <div className="panel results-panel">
                    <div className="panel-header">
                        <UserCheck size={20} />
                        Live Verification Stream
                    </div>

                    <div className="panel-content empty-results">
                        {!capturedImage && !isVerifying && (
                            <div className="empty-state">
                                <Scan size={64} className="scan-frame" />
                                <h3>Waiting for student...</h3>
                                <p>System will auto-detect when a student approaches.</p>
                            </div>
                        )}

                        {isVerifying && (
                            <div className="success-state">
                                <img src={capturedImage} alt="Captured" className="captured-preview" style={{ opacity: 0.5 }} />
                                <div className="status-badge" style={{ backgroundColor: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1' }}>
                                    <Loader2 size={16} className="animate-spin" />
                                    Analyzing Face...
                                </div>
                            </div>
                        )}

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
                                        Identity Unknown
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