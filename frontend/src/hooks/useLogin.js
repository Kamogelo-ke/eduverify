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

        try {
            // UPDATED: Point directly to your FastAPI backend URL
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: email,
                    password: password,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.detail || 'Login failed');
                setIsLoggingIn(false);
                return;
            }

            // Save token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            setIsLoggingIn(false);

            // Route based on backend role
            if (data.user.role === 'admin') {
                navigate('/admin-dashboard');
            } else {
                navigate('/override'); // Or wherever invigilators go
            }

        } catch (error) {
            console.error(error);
            alert('Server error: Make sure your Docker backend is running!');
            setIsLoggingIn(false);
        }
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