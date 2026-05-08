// src/hooks/useStudentScanner.js
import { useState } from 'react';

export const useStudentScanner = () => {
    const [isVerifying, setIsVerifying] = useState(false);

    // Helper function to convert the base64 image from the webcam into a File blob
    const base64ToBlob = async (base64) => {
        const response = await fetch(base64);
        return await response.blob();
    };

    const verifyStudentFace = async (examId, imageBase64) => {
        setIsVerifying(true);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Authentication required. Please log in again.');
            }

            const imageBlob = await base64ToBlob(imageBase64);

            const formData = new FormData();
            formData.append('image', imageBlob, 'student_capture.jpg');

            if (examId) {
                formData.append('exam_session_id', examId);
            }
            formData.append('terminal_id', 'Web-Scanner-01');

            // 👇 UPDATED: Using relative path! Vite will proxy this to localhost:8000
            const response = await fetch('/api/v1/face/verify', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Reminder: Do NOT set 'Content-Type' when using FormData
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok && !data) {
                throw new Error('Verification failed on the server.');
            }

            return data;

        } catch (error) {
            console.error("Error sending face to backend:", error);
            return {
                outcome: "error",
                outcome_reason: error.message || "Network or server error"
            };
        } finally {
            setIsVerifying(false);
        }
    };

    return {
        verifyStudentFace,
        isVerifying
    };
};