import { useState, useEffect } from 'react';
import { api } from '../utils/api';

export const useAdminDashboard = () => {
    const [stats, setStats] = useState({
        totalStudents: 0,
        faceRegistered: 0,
        totalExams: 0,
        activeExams: 0,
        todaysVerifications: 0,
        successRate: '0%',
    });
    const [recentVerifications, setRecentVerifications] = useState([]);
    const [upcomingExams, setUpcomingExams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsData, attemptsData, sessionsData] = await Promise.all([
                    api.get('/admin/stats'),
                    api.get('/admin/reports/attempts?page_size=10'),
                    api.get('/admin/exam-sessions'),
                ]);

                const total = statsData.total_attempts_today ?? 0;
                const granted = statsData.granted_today ?? 0;

                setStats({
                    totalStudents: statsData.total_students ?? 0,
                    faceRegistered: statsData.enrolled_students ?? 0,
                    totalExams: Array.isArray(sessionsData) ? sessionsData.length : 0,
                    activeExams: statsData.active_exam_sessions ?? 0,
                    todaysVerifications: total,
                    successRate: total > 0 ? `${Math.round((granted / total) * 100)}%` : '0%',
                });

                setRecentVerifications(
                    (attemptsData.attempts || []).map(a => ({
                        time: new Date(a.attempted_at).toLocaleTimeString(),
                        student: a.student_name || 'Unknown',
                        exam: a.exam_session || 'N/A',
                        status: a.outcome === 'granted' ? 'GRANTED' : a.was_overridden ? 'OVERRIDE' : 'FAILED',
                        confidence: a.face_similarity_score != null
                            ? `${Math.round(a.face_similarity_score * 100)}%`
                            : 'N/A',
                        message: a.outcome,
                    }))
                );

                setUpcomingExams(
                    (Array.isArray(sessionsData) ? sessionsData : []).slice(0, 5).map(s => ({
                        code: s.module_code,
                        name: s.module_name,
                        faculty: '',
                        venue: s.venue,
                        duration: '',
                        date: s.scheduled_start
                            ? new Date(s.scheduled_start).toLocaleDateString()
                            : 'TBD',
                        time: s.scheduled_start
                            ? new Date(s.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                            : 'TBD',
                    }))
                );
            } catch (err) {
                setError(err.message);
                console.error('Dashboard fetch error:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    return { stats, recentVerifications, upcomingExams, loading, error };
};
