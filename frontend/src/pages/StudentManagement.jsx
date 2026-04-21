import React from 'react';
import { Users, BookOpen, Search, CheckCircle, XCircle } from 'lucide-react';

// Custom Hook
import { useStudents } from '../hooks/useStudents'; 

// Shared Components
import Header from '../components/Header';
import Footer from '../components/Footer';

// Styles
import '../styles/pages/student-management.scss';

const StudentManagement = () => {
  const { 
    students, 
    searchTerm, 
    handleSearchChange 
  } = useStudents();

  return (
    <div className="dashboard-wrapper">
      <Header />

      <main className="content-area">
        <div className="tab-row">
          <button className="active"><Users size={18} /> Students</button>
          <button className="inactive"><BookOpen size={18} /> Exams</button>
        </div>

        <section className="main-card">
          <header>
            <div className="title">
              <Users size={20} /> 
              <h2>Student List</h2>
            </div>
          </header>

          <div className="table-container">
            <div className="search-box">
              <Search className="icon" size={18} />
              <input 
                type="text" 
                placeholder="Search students by name, number, or email..." 
                value={searchTerm}
                onChange={handleSearchChange}
              />
            </div>

            <table>
              <thead>
                <tr>
                  <th>Student #</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Faculty</th>
                  <th>Program</th>
                  <th>Face</th>
                  <th>Exams</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id}>
                    <td className="bold">{student.id}</td>
                    <td>{student.name}</td>
                    <td>{student.email}</td>
                    <td>{student.faculty}</td>
                    <td>{student.program}</td>
                    <td>
                      {student.face === "Registered" ? (
                        <span className="badge registered"><CheckCircle size={14} /> Registered</span>
                      ) : (
                        <span className="badge not-set"><XCircle size={14} /> Not Set</span>
                      )}
                    </td>
                    <td>{student.exams}</td>
                  </tr>
                ))}
                {students.length === 0 && (
                  <tr>
                    <td colSpan="7" className="no-results">
                      No students found matching your search.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default StudentManagement;