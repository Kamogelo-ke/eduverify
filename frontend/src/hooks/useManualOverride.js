import { useState, useRef, useEffect } from 'react';
import { api } from '../utils/api';

export const useManualOverride = () => {
    const [deniedStudents, setDeniedStudents] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [loading, setLoading] = useState(true);

    const [isCapturing, setIsCapturing] = useState(false);
    const [evidenceImage, setEvidenceImage] = useState(null);

    const videoRef = useRef(null);
    const streamRef = useRef(null);

    useEffect(() => {
        fetchDeniedStudents();
        return () => stopCamera();
    }, []);

    const fetchDeniedStudents = async () => {
        try {
            const data = await api.get('/admin/reports/attempts?outcome=denied_identity&page_size=50');
            setDeniedStudents(
                (data.attempts || [])
                    .filter(a => !a.was_overridden)
                    .map(a => ({
                        attemptId: a.attempt_id,
                        id: a.student_number || 'Unknown',
                        name: a.student_name || 'Unknown Student',
                        time: new Date(a.attempted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        reason: a.outcome === 'denied_identity' ? 'Face Not A Match' : a.outcome,
                        registeredImage: null,
                    }))
            );
        } catch (err) {
            console.error('Failed to fetch denied students:', err);
        } finally {
            setLoading(false);
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    };

    const handleSelectStudent = (student) => {
        setSelectedStudent(student);
        setEvidenceImage(null);
        setIsCapturing(false);
        stopCamera();
    };

    const startInvestigation = async () => {
        setIsCapturing(true);
        setEvidenceImage(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (err) {
            console.error('Camera error:', err);
            alert('Could not access the webcam for investigation.');
            setIsCapturing(false);
        }
    };

    const captureAndGrant = async () => {
        if (!videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext('2d').drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        setEvidenceImage(canvas.toDataURL('image/jpeg'));
        stopCamera();

        try {
            await api.post('/face/override', {
                attempt_id: selectedStudent.attemptId,
                reason: 'Manual override by invigilator after physical ID verification',
            });

            setTimeout(() => {
                alert(`Access Granted to ${selectedStudent.name}. Evidence logged.`);
                setDeniedStudents(prev => prev.filter(s => s.attemptId !== selectedStudent.attemptId));
                setSelectedStudent(null);
                setIsCapturing(false);
                setEvidenceImage(null);
            }, 500);
        } catch (err) {
            alert(`Override failed: ${err.message}`);
        }
    };

    const denyPermanently = () => {
        if (window.confirm(`Are you sure you want to permanently deny ${selectedStudent.name}?`)) {
            setDeniedStudents(prev => prev.filter(s => s.attemptId !== selectedStudent.attemptId));
            setSelectedStudent(null);
        }
    };

    return {
        deniedStudents,
        selectedStudent,
        isCapturing,
        evidenceImage,
        videoRef,
        loading,
        handleSelectStudent,
        startInvestigation,
        captureAndGrant,
        denyPermanently,
    };
};
