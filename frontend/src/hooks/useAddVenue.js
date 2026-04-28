// // src/hooks/useAddVenue.js
// import { useState } from "react";

// const INITIAL_STATE = {
//   venueName: "",
//   capacity: "",
//   location: "",
//   courseCode: "",
//   moduleName: "",
//   date: "",
//   time: "",
//   invigilators: []
// };

// export const useAddVenue = () => {
//   const [formData, setFormData] = useState(INITIAL_STATE);

//   const invigilatorList = [
//     "Ms. Sambo",
//     "Ms. Nthabeni",
//     "Mr. Khumalo",
//     "Mrs. Lesego",
//     "Dr. Thlong"
//   ];

//   // Handle input changes
//   const handleChange = (e) => {
//     const { name, value } = e.target;
//     setFormData(prev => ({
//       ...prev,
//       [name]: value
//     }));
//   };

//   // Handle invigilator selection
//   const handleInvigilatorChange = (name) => {
//     setFormData(prev => ({
//       ...prev,
//       invigilators: prev.invigilators.includes(name)
//         ? prev.invigilators.filter(i => i !== name)
//         : [...prev.invigilators, name]
//     }));
//   };

//   // Reset form
//   const resetForm = () => {
//     setFormData(INITIAL_STATE);
//   };

//   // Submit handler
//   const handleSubmit = (e) => {
//     e.preventDefault();

//     // Basic validation
//     if (!formData.venueName || !formData.courseCode || !formData.date) {
//       alert("Please fill in all required fields");
//       return;
//     }

//     console.log("Submitting Venue:", formData);

//     // TODO: send to backend API

//     resetForm();
//   };

//   return {
//     formData,
//     invigilatorList,
//     handleChange,
//     handleInvigilatorChange,
//     handleSubmit
//   };
// };

import { useState } from "react";

export const useAddVenue = () => {
  // 1. Define the initial state of the form
  // Removed 'location', added 'startTime' and 'endTime'
  const [formData, setFormData] = useState({
    venueName: "",
    capacity: "",
    courseCode: "",
    date: "",
    startTime: "",
    endTime: "",
    invigilators: [],
  });

  // 2. Dummy list of available invigilators to choose from
  const [invigilatorList] = useState([
    "Dr. Khumalo",
    "Prof. Khoza",
    "Mr. Thlong",
    "Ms. Nthabeni",
    "Mrs. Sambo",
    "Mr. Molalatladi",
  ]);

  // 3. Handle standard input changes (text, number, date, time)
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // 4. Handle checkbox logic for multiple invigilators
  const handleInvigilatorChange = (name) => {
    setFormData((prev) => {
      const isAlreadySelected = prev.invigilators.includes(name);
      if (isAlreadySelected) {
        // Remove if already in the list
        return {
          ...prev,
          invigilators: prev.invigilators.filter((inv) => inv !== name),
        };
      } else {
        // Add to the list
        return {
          ...prev,
          invigilators: [...prev.invigilators, name],
        };
      }
    });
  };

  // 5. Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Simple validation check
    if (!formData.venueName || !formData.courseCode || !formData.startTime) {
      alert("Please fill in all required fields.");
      return;
    }

    console.log("Exam Scheduled Successfully:", formData);
    alert(`Exam for ${formData.courseCode} has been assigned to ${formData.venueName}`);
    
    // Reset form after submission
    setFormData({
      venueName: "",
      capacity: "",
      courseCode: "",
      date: "",
      startTime: "",
      endTime: "",
      invigilators: [],
    });
  };

  return {
    formData,
    invigilatorList,
    handleChange,
    handleInvigilatorChange,
    handleSubmit,
  };
};