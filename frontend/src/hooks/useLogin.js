import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const useLogin = () => {
    const navigate = useNavigate();
    const [role, setRole] = useState('invigilator');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoggingIn, setIsLoggingIn] = useState(false);

    const handleRoleChange = (selectedRole) => {
        setRole(selectedRole);
        // Optional: clear the form when they switch roles
        setEmail('');
        setPassword('');
    };

    const submitLogin = async (e) => {
        e.preventDefault();
        setIsLoggingIn(true);

        // Simulate a brief API call/verification delay
        setTimeout(() => {
            setIsLoggingIn(false);

            // Route based on role
            if (role === 'admin') {
                navigate('/students'); // Admins go to the Student Management dashboard
            } else {
                navigate('/scanner');   // Invigilators go straight to the face scanner
            }
        }, 800);
    };

    return {
        role,
        handleRoleChange,
        email,
        setEmail,
        password,
        setPassword,
        submitLogin,
        isLoggingIn
    };
};