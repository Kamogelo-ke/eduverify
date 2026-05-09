import { useState, useEffect } from 'react';
import { api } from '../utils/api';

export const useEntranceMonitor = () => {
    const [scans, setScans] = useState([]);
    const [stats, setStats] = useState({ total: 0, granted: 0, denied: 0, overrides: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchScans = async () => {
            try {
                const data = await api.get('/admin/reports/attempts?page_size=20');
                const attempts = data.attempts || [];

                setScans(
                    attempts.map((a, i) => ({
                        id: i + 1,
                        name: a.student_name || 'Unknown',
                        studentNo: a.student_number || 'N/A',
                        status: a.was_overridden ? 'Override' : a.outcome === 'granted' ? 'Granted' : 'Denied',
                        time: new Date(a.attempted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    }))
                );

                const granted = attempts.filter(a => a.outcome === 'granted').length;
                const overrides = attempts.filter(a => a.was_overridden).length;
                const denied = attempts.filter(a => a.outcome !== 'granted' && !a.was_overridden).length;
                setStats({ total: data.total ?? attempts.length, granted, denied, overrides });
            } catch (err) {
                console.error('Failed to fetch entrance monitor data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchScans();
    }, []);

    return { scans, stats, loading };
};
