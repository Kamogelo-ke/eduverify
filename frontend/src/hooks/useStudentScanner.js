// src/hooks/useStudentScanner.js
import { useState } from 'react';

function base64ToBlob(base64, mimeType = 'image/jpeg') {
    const raw = base64.includes(',') ? base64.split(',')[1] : base64;
    const bytes = atob(raw);
    const buffer = new ArrayBuffer(bytes.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < bytes.length; i++) view[i] = bytes.charCodeAt(i);
    return new Blob([buffer], { type: mimeType });
}

export const useStudentScanner = () => {
    const [isVerifying, setIsVerifying] = useState(false);

    const verifyStudentFace = async (examId, imageBase64, studentNumber = null) => {
        setIsVerifying(true);
        try {
            const token = localStorage.getItem('authToken');
            const formData = new FormData();
            formData.append('image', base64ToBlob(imageBase64), 'capture.jpg');
            if (studentNumber) formData.append('student_number', studentNumber);
            if (examId) formData.append('exam_session_id', String(examId));

            const response = await fetch('/api/v1/face/verify', {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });

            const data = await response.json();

            if (!response.ok && !data) {
                throw new Error('Verification failed on the server.');
            }

            return data;
        } catch (error) {
            console.error('Error sending face to backend:', error);
            return { success: false, error: true };
        } finally {
            setIsVerifying(false);
        }
    };

    return { verifyStudentFace, isVerifying };
};
