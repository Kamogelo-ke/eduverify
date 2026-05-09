import { useState } from 'react';
import { api } from '../utils/api';

const EMPTY_FORM = {
    venueName: '',
    capacity: '',
    courseCode: '',
    moduleName: '',
    date: '',
    startTime: '',
    endTime: '',
    invigilators: [],
};

export const useAddVenue = () => {
    const [formData, setFormData] = useState(EMPTY_FORM);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [invigilatorList] = useState([
        'Dr. Khumalo',
        'Prof. Khoza',
        'Mr. Thlong',
        'Ms. Nthabeni',
        'Mrs. Sambo',
        'Mr. Molalatladi',
    ]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleInvigilatorChange = (name) => {
        setFormData(prev => ({
            ...prev,
            invigilators: prev.invigilators.includes(name)
                ? prev.invigilators.filter(i => i !== name)
                : [...prev.invigilators, name],
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.venueName || !formData.courseCode || !formData.date || !formData.startTime || !formData.endTime) {
            alert('Please fill in all required fields.');
            return;
        }

        setIsSubmitting(true);
        try {
            await api.post('/admin/exam-session', {
                module_code: formData.courseCode,
                module_name: formData.moduleName || formData.courseCode,
                venue: formData.venueName,
                scheduled_start: `${formData.date}T${formData.startTime}:00`,
                scheduled_end: `${formData.date}T${formData.endTime}:00`,
            });

            alert(`Exam for ${formData.courseCode} has been assigned to ${formData.venueName}`);
            setFormData(EMPTY_FORM);
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return {
        formData,
        invigilatorList,
        isSubmitting,
        handleChange,
        handleInvigilatorChange,
        handleSubmit,
    };
};
