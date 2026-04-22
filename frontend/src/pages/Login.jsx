import React from 'react';
import { User, Lock, ArrowRight, ScanFace, Loader2 } from 'lucide-react';

// Import Layout Components
import Header2 from '../components/Header2';
import Footer from '../components/Footer';

// Import Hook & Styles
import { useLogin } from '../hooks/useLogin';
import '../styles/pages/_login.scss';

const Login = () => {
    const {
        role,
        handleRoleChange,
        email,
        setEmail,
        password,
        setPassword,
        submitLogin,
        isLoggingIn
    } = useLogin();

    return (
        <div className="dashboard-wrapper">
            <Header2 />

            <div className="login-page-container">
                <div className="login-card">

                    <div className="brand-header">
                        <div className="logo">
                            <div className="icon-box">
                                <ScanFace size={24} />
                            </div>
                            <h2>EduVerify</h2>
                        </div>
                        <div className="welcome-text">
                            <h1>Welcome back</h1>
                            <p>Sign in to access the verification system</p>
                        </div>
                    </div>

                    <div className="role-toggle">
                        <button
                            className={role === 'invigilator' ? 'active' : ''}
                            onClick={() => handleRoleChange('invigilator')}
                            type="button"
                        >
                            Invigilator
                        </button>
                        <button
                            className={role === 'admin' ? 'active' : ''}
                            onClick={() => handleRoleChange('admin')}
                            type="button"
                        >
                            Admin
                        </button>
                    </div>

                    <form className="login-form" onSubmit={submitLogin}>
                        <div className="form-group">
                            <label>Email or Staff ID</label>
                            <div className="input-wrapper">
                                <User size={18} className="input-icon" />
                                <input
                                    type="text"
                                    placeholder={role === 'admin' ? "admin@tut.ac.za" : "staff@tut.ac.za"}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Password</label>
                            <div className="input-wrapper">
                                <Lock size={18} className="input-icon" />
                                <input
                                    type="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <button type="submit" className="btn-submit" disabled={isLoggingIn}>
                            {isLoggingIn ? (
                                <>Verifying... <Loader2 size={18} className="animate-spin" /></>
                            ) : (
                                <>Sign In <ArrowRight size={18} /></>
                            )}
                        </button>
                    </form>

                    <div className="login-footer">
                        Authorized personnel only. All access attempts are logged.
                    </div>
                </div>
            </div>

            <Footer />
        </div>
    );
};

export default Login;