import { useState, useEffect } from 'react';
import { api } from '../utils/api';

export const useVenues = () => {
    const [venues, setVenues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingVenue, setEditingVenue] = useState(null);

    useEffect(() => {
        const fetchVenues = async () => {
            try {
                const data = await api.get('/admin/exam-sessions?upcoming_only=false');
                setVenues(
                    (Array.isArray(data) ? data : []).map(s => ({
                        id: s.id,
                        venueName: s.venue,
                        location: '',
                        courseCode: s.module_code,
                        moduleName: s.module_name,
                        date: s.scheduled_start
                            ? new Date(s.scheduled_start).toISOString().split('T')[0]
                            : '',
                        time: s.scheduled_start
                            ? new Date(s.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                            : '',
                        invigilators: [],
                    }))
                );
            } catch (err) {
                console.error('Failed to fetch venues:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchVenues();
    }, []);

    const deleteVenue = (id) => {
        if (window.confirm('Are you sure you want to remove this exam assignment?')) {
            setVenues(prev => prev.filter(v => v.id !== id));
        }
    };

    const startEdit = (venue) => setEditingVenue({ ...venue });

    const handleEditChange = (e) => {
        const { name, value } = e.target;
        setEditingVenue(prev => ({ ...prev, [name]: value }));
    };

    const saveEdit = () => {
        setVenues(prev => prev.map(v => v.id === editingVenue.id ? editingVenue : v));
        setEditingVenue(null);
    };

    return {
        venues,
        editingVenue,
        loading,
        deleteVenue,
        startEdit,
        handleEditChange,
        saveEdit,
        setEditingVenue,
    };
};
