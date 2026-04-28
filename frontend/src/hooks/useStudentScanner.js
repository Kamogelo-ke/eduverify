// src/hooks/useStudentScanner.js
import { useState } from 'react';

export const useStudentScanner = () => {
    const [isVerifying, setIsVerifying] = useState(false);

    const verifyStudentFace = async (examId, imageBase64) => {
        setIsVerifying(true);
        try {
            const response = await fetch('http://localhost:5000/api/verify-face', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    examId: examId,
                    image: imageBase64
                })
            });

            // Always try to parse the JSON first, even if response.ok is false,
            // because the backend might be sending { noFaceDetected: true } alongside an error code.
            const data = await response.json();

            // If it's a server crash AND there's no useful data, then throw an error
            if (!response.ok && !data) {
                throw new Error('Verification failed on the server.');
            }

            return data; // Returns the result (including failure reasons) to your component

        } catch (error) {
            console.error("Error sending face to backend:", error);
            // Return a fallback object so the frontend doesn't crash completely
            return { success: false, error: true };
        } finally {
            setIsVerifying(false);
        }
    };

    return {
        verifyStudentFace,
        isVerifying
    };
};