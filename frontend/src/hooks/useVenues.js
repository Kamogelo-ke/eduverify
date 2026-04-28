import { useState, useEffect } from "react";

export const useVenues = () => {
  // Initial dummy data to match your "Scheduled Exam" logic
  const [venues, setVenues] = useState([
    {
      id: 1,
      venueName: "Gencor Hall",
      location: "Soshanguve South",
      courseCode: "DSO34BT",
      moduleName: "Development Software III",
      date: "2026-05-15",
      time: "09:00",
      invigilators: ["John Doe", "Sarah Smith"]
    },
    {
      id: 2,
      venueName: "Building 4-102",
      location: "Soshanguve North",
      courseCode: "tpz201t",
      moduleName: "Technical Programming II",
      date: "2026-05-16",
      time: "14:00",
      invigilators: ["Mike Ross"]
    }
  ]);

  // State for the Edit Modal
  const [editingVenue, setEditingVenue] = useState(null);

  // --- ACTIONS ---

  // Delete a scheduled exam
  const deleteVenue = (id) => {
    if (window.confirm("Are you sure you want to remove this exam assignment?")) {
      setVenues(venues.filter((v) => v.id !== id));
    }
  };

  // Open the edit modal with the selected venue's data
  const startEdit = (venue) => {
    setEditingVenue({ ...venue });
  };

  // Handle input changes inside the Edit Modal
  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditingVenue((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Save the edited changes back to the list
  const saveEdit = () => {
    setVenues((prevVenues) =>
      prevVenues.map((v) => (v.id === editingVenue.id ? editingVenue : v))
    );
    setEditingVenue(null); // Close modal
  };

  return {
    venues,
    editingVenue,
    deleteVenue,
    startEdit,
    handleEditChange,
    saveEdit,
    setEditingVenue,
  };
};