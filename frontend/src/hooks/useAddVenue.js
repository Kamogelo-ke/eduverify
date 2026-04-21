// src/hooks/useAddVenue.js
import { useState } from "react";

const INITIAL_STATE = {
  venueName: "",
  capacity: "",
  location: "",
  courseCode: "",
  moduleName: "",
  date: "",
  time: "",
  invigilators: []
};

export const useAddVenue = () => {
  const [formData, setFormData] = useState(INITIAL_STATE);

  const invigilatorList = [
    "Ms. Sambo",
    "Ms. Nthabeni",
    "Mr. Khumalo",
    "Mrs. Lesego",
    "Dr. Thlong"
  ];

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle invigilator selection
  const handleInvigilatorChange = (name) => {
    setFormData(prev => ({
      ...prev,
      invigilators: prev.invigilators.includes(name)
        ? prev.invigilators.filter(i => i !== name)
        : [...prev.invigilators, name]
    }));
  };

  // Reset form
  const resetForm = () => {
    setFormData(INITIAL_STATE);
  };

  // Submit handler
  const handleSubmit = (e) => {
    e.preventDefault();

    // Basic validation
    if (!formData.venueName || !formData.courseCode || !formData.date) {
      alert("Please fill in all required fields");
      return;
    }

    console.log("Submitting Venue:", formData);

    // TODO: send to backend API

    resetForm();
  };

  return {
    formData,
    invigilatorList,
    handleChange,
    handleInvigilatorChange,
    handleSubmit
  };
};