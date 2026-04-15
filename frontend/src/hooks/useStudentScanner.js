// src/hooks/useStudentScanner.js
import { useState } from 'react';

export const useStudentScanner = () => {
    const [isVerifying, setIsVerifying] = useState(false);

    const verifyStudentFace = async (examId, imageBase64) => {
        setIsVerifying(true);
        try {
            // Replace with your actual backend URL
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

            if (!response.ok) {
                throw new Error('Verification failed on the server.');
            }

            const data = await response.json();
            return data; // Returns the result to your component

        } catch (error) {
            console.error("Error sending face to backend:", error);
            throw error;
        } finally {
            setIsVerifying(false);
        }
    };

    return {
        verifyStudentFace,
        isVerifying
    };
};