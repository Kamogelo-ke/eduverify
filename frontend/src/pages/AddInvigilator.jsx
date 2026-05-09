import React, { useState } from 'react';
import { UserPlus, ArrowLeft } from 'lucide-react'; // Remember to import your new icon choice here
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import '../styles/pages/invigilator.scss';

const AddInvigilator = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    staffNumber: '',
    fullName: '',
    email: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    try {
      await api.post('/admin/users', {
        email: formData.email,
        full_name: formData.fullName,
        role: 'invigilator',
      });
      alert(`Invigilator ${formData.fullName} added. A temporary password has been emailed to ${formData.email}.`);
      navigate('/admin-dashboard');
    } catch (err) {
      setError(err.message || 'Failed to add invigilator.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="dashboard-wrapper">
      <Header />
      
      <main className="content-area">

        <section className="main-card invigilator-card">
          <header>
            <div className="title">
              <UserPlus size={20} /> 
              <h2>Add New Invigilator</h2>
            </div>
          </header>

          <div className="card-content">
            <form className="registration-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Staff Number</label>
                <input 
                  type="text" 
                  placeholder="e.g. EMP12345" 
                  required 
                  onChange={(e) => setFormData({...formData, staffNumber: e.target.value})}
                />
              </div>
              
              <div className="form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  placeholder="e.g. John Doe" 
                  required 
                  onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Email Address</label>
                <input 
                  type="email" 
                  placeholder="staffname@tut.ac.za" 
                  required 
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>

              {error && (
                <p style={{ color: '#e53e3e', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{error}</p>
              )}
              <button type="submit" className="btn-submit" disabled={isSubmitting}>
                {isSubmitting ? 'Adding...' : 'Register Invigilator'}
              </button>
            </form>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default AddInvigilator;