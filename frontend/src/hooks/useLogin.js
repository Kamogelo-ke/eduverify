import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const useLogin = () => {
    const navigate = useNavigate();
    const [role, setRole] = useState('invigilator');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoggingIn, setIsLoggingIn] = useState(false);
    const [error, setError] = useState('');

    const handleRoleChange = (selectedRole) => {
        setRole(selectedRole);
        setEmail('');
        setPassword('');
        setError('');
    };

    const submitLogin = async (e) => {
        e.preventDefault();
        setIsLoggingIn(true);
        setError('');

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('userRole', data.user.role);
            localStorage.setItem('userName', `${data.user.first_name} ${data.user.last_name}`);

            if (data.user.role === 'admin') {
                navigate('/admin-dashboard');
            } else {
                navigate('/override');
            }
        } catch (err) {
            setError(err.message || 'Invalid credentials. Please try again.');
        } finally {
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
        isLoggingIn,
        error,
    };
};
