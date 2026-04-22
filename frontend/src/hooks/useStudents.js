import { useState, useMemo } from 'react';

// Initial data based on your screenshot
const INITIAL_STUDENTS = [
  { id: '2023018456', name: 'Thabo Mokoena', email: 'mokoenat@tut4life.ac.za', faculty: 'Faculty of ICT', program: 'Diploma in Computer Science', face: 'Not Set', exams: 2 },
  { id: '2022029347', name: 'Nomvula Ndlovu', email: 'ndlovun@tut4life.ac.za', faculty: 'Faculty of Engineering', program: 'BEng in Mechanical Engineering', face: 'Not Set', exams: 0 },
  { id: '2024031234', name: 'Sipho Zulu', email: 'zulus@tut4life.ac.za', faculty: 'Faculty of ICT', program: 'Bachelor of Information Technology', face: 'Not Set', exams: 2 },
  { id: '2023015678', name: 'Lerato Khumalo', email: 'khumalol@tut4life.ac.za', faculty: 'Faculty of Science', program: 'BSc in Biotechnology', face: 'Not Set', exams: 1 },
];

export const useStudents = () => {
  const [students] = useState(INITIAL_STUDENTS);
  const [searchTerm, setSearchTerm] = useState('');

  // Handles searching across ID, Name, and Email
  const filteredStudents = useMemo(() => {
    return students.filter((student) => {
      const searchStr = searchTerm.toLowerCase();
      return (
        student.name.toLowerCase().includes(searchStr) ||
        student.id.includes(searchStr) ||
        student.email.toLowerCase().includes(searchStr)
      );
    });
  }, [students, searchTerm]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  return {
    students: filteredStudents,
    searchTerm,
    handleSearchChange,
    totalCount: students.length
  };
};