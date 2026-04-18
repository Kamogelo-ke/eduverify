import { useState } from 'react';

export const useAdminDashboard = () => {

  const [stats] = useState({
    totalStudents: 6,
    faceRegistered: 1,
    totalExams: 5,
    activeExams: 5,
    todaysVerifications: 1,
    successRate: "0%"
  });

  const [recentVerifications] = useState([
    {
      time: "13:08:01",
      student: "Kamo Thlong",
      exam: "CMPG201",
      status: "FAILED",
      confidence: "69%",
      message: "Student not registered for exam"
    }
  ]);

  const [upcomingExams] = useState([
    {
      code: "CMPG101",
      name: "Computer Programming 1A",
      faculty: "Faculty of ICT",
      venue: "ICT Lab 3A",
      duration: "180 minutes",
      date: "2026/04/15",
      time: "09:00"
    }
  ]);

  return {
    stats,
    recentVerifications,
    upcomingExams
  };
};