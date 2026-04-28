import { useState, useRef, useEffect } from 'react';

// Mock data: Students who just failed the auto-scanner
// Mock data: Students who just failed the auto-scanner
const INITIAL_DENIED_LIST = [
    {
        id: '2024031234',
        name: 'Sipho Zulu',
        time: '08:14 AM',
        reason: 'Face Not A Match',
        registeredImage: 'https://static.vecteezy.com/system/resources/previews/036/442/721/non_2x/ai-generated-portrait-of-a-young-man-no-facial-expression-facing-the-camera-isolated-white-background-ai-generative-photo.jpg' // Added mock photo
    },
    {
        id: '2022029347',
        name: 'Nomvula Ndlovu',
        time: '08:05 AM',
        reason: 'Face Not A Match',
        registeredImage: 'https://static.vecteezy.com/system/resources/previews/036/442/721/non_2x/ai-generated-portrait-of-a-young-man-no-facial-expression-facing-the-camera-isolated-white-background-ai-generative-photo.jpg' // Added mock photo
    }
];

export const useManualOverride = () => {
    const [deniedStudents, setDeniedStudents] = useState(INITIAL_DENIED_LIST);
    const [selectedStudent, setSelectedStudent] = useState(null);

    // Camera State
    const [isCapturing, setIsCapturing] = useState(false);
    const [evidenceImage, setEvidenceImage] = useState(null);

    const videoRef = useRef(null);
    const streamRef = useRef(null);

    // Stop camera when unmounting or switching students
    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    };

    useEffect(() => {
        return () => stopCamera();
    }, []);

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
            console.error("Camera error:", err);
            alert("Could not access the webcam for investigation.");
            setIsCapturing(false);
        }
    };

    const captureAndGrant = () => {
        if (!videoRef.current) return;

        // 1. Take the picture
        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');

        // Ensure the drawing matches the video dimensions exactly
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const imageUrl = canvas.toDataURL('image/jpeg');

        setEvidenceImage(imageUrl);
        stopCamera();

        // 2. Here you would normally send the override data to your backend API
        // console.log("Evidence saved for:", selectedStudent.id, imageUrl);

        // 3. Remove student from queue and reset
        setTimeout(() => {
            alert(`Access Granted to ${selectedStudent.name}. Evidence logged.`);
            setDeniedStudents(prev => prev.filter(s => s.id !== selectedStudent.id));
            setSelectedStudent(null);
            setIsCapturing(false);
            setEvidenceImage(null);
        }, 500);
    };

    const denyPermanently = () => {
        if (window.confirm(`Are you sure you want to permanently deny ${selectedStudent.name}?`)) {
            setDeniedStudents(prev => prev.filter(s => s.id !== selectedStudent.id));
            setSelectedStudent(null);
        }
    };

    return {
        deniedStudents,
        selectedStudent,
        isCapturing,
        evidenceImage,
        videoRef,
        handleSelectStudent,
        startInvestigation,
        captureAndGrant,
        denyPermanently
    };
};