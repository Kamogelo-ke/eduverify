import { useState, useEffect, useMemo } from 'react';
import { api } from '../utils/api';

export const useStudents = () => {
    const [allStudents, setAllStudents] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStudents = async () => {
            try {
                const data = await api.get('/students/?page_size=100');
                setAllStudents(
                    (data.students || []).map(s => ({
                        id: s.student_number,
                        name: s.full_name,
                        email: s.email,
                        faculty: '',
                        program: s.programme || '',
                        face: s.has_biometric_profile ? 'Registered' : 'Not Set',
                        exams: 0,
                    }))
                );
            } catch (err) {
                setError(err.message);
                console.error('Failed to fetch students:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchStudents();
    }, []);

    const filteredStudents = useMemo(() => {
        const searchStr = searchTerm.toLowerCase();
        return allStudents.filter(s =>
            s.name.toLowerCase().includes(searchStr) ||
            s.id.toLowerCase().includes(searchStr) ||
            s.email.toLowerCase().includes(searchStr)
        );
    }, [allStudents, searchTerm]);

    const handleSearchChange = (e) => setSearchTerm(e.target.value);

    return {
        students: filteredStudents,
        searchTerm,
        handleSearchChange,
        totalCount: allStudents.length,
        loading,
        error,
    };
};
