// import React from "react";
// import { MapPin, ClipboardList, PlusCircle, Save, Settings, Users } from 'lucide-react';
// import { useNavigate } from "react-router-dom";
// import Header from "../components/Header";
// import Footer from "../components/Footer";
// import { useAddVenue } from "../hooks/useAddVenue";

// import "../styles/pages/AddVenue.scss";

// const AddVenue = () => {
//   const navigate = useNavigate();
//   const {
//     formData,
//     invigilatorList,
//     handleChange,
//     handleInvigilatorChange,
//     handleSubmit
//   } = useAddVenue();

//   return (
//     <div className="dashboard-wrapper">
//       <Header />

//       <main className="content-area">
//         {/* Navigation Tabs */}
//         <div className="tab-row">
//           <button className="inactive" onClick={() => navigate('/manage-venues')}>
//             <Settings size={18} /> Manage Scheduled Exams
//           </button>
//           <button className="active">
//             <PlusCircle size={18} /> Schedule New Exam
//           </button>
//         </div>

//         {/* ONE CONTINUOUS WHITE CONTAINER */}
//         <section className="main-card">
//           <header>
//             <div className="title">
//               <PlusCircle size={20} /> 
//               <h2>Assign Exam to Venue</h2>
//             </div>
//           </header>

//           <form className="form-body" onSubmit={handleSubmit}>
            
//             <div className="form-grid">
//               {/* VENUE SECTION */}
//               <div className="form-section">
//                 <h3>Venue Information</h3>
//                 <div className="input-group">
//                   <label>Venue Name</label>
//                   <input type="text" name="venueName" value={formData.venueName} onChange={handleChange} />
//                 </div>
//                 <div className="row">
//                   <div className="input-group">
//                     <label>Seating Capacity</label>
//                     <input type="number" name="capacity" value={formData.capacity} onChange={handleChange} />
//                   </div>
//                   <div className="input-group">
//                     <label>Location</label>
//                     <input type="text" name="location" value={formData.location} onChange={handleChange} />
//                   </div>
//                 </div>
//               </div>

//               {/* EXAM SECTION */}
//               <div className="form-section">
//                 <h3>Exam Details</h3>
//                 <div className="input-group">
//                   <label>Course Code</label>
//                   <input type="text" name="courseCode" value={formData.courseCode} onChange={handleChange} />
//                 </div>
//                 <div className="input-group">
//                   <label>Module Name</label>
//                   <input type="text" name="moduleName" value={formData.moduleName} onChange={handleChange} />
//                 </div>
//                 <div className="row">
//                   <div className="input-group">
//                     <label>Date</label>
//                     <input type="date" name="date" value={formData.date} onChange={handleChange} />
//                   </div>
//                   <div className="input-group">
//                     <label>Time</label>
//                     <input type="time" name="time" value={formData.time} onChange={handleChange} />
//                   </div>
//                 </div>
//               </div>
//             </div>

//             {/* INVIGILATORS SECTION */}
//             <div className="form-section full-width">
//               <h3>Assign Invigilators</h3>
//               <div className="invigilators-grid">
//                 {invigilatorList.map((inv, index) => (
//                   <label key={index} className="checkbox-card">
//                     <input 
//                       type="checkbox" 
//                       checked={formData.invigilators.includes(inv)} 
//                       onChange={() => handleInvigilatorChange(inv)} 
//                     />
//                     <span>{inv}</span>
//                   </label>
//                 ))}
//               </div>
//             </div>

//             <div className="form-actions">
//               <button type="submit" className="save-btn">
//                 <Save size={18} /> Finalize Assignment
//               </button>
//             </div>
//           </form>
//         </section>
//       </main>

//       <Footer />
//     </div>
//   );
// };

// export default AddVenue;

import React from "react";
import { MapPin, ClipboardList, PlusCircle, Save, Settings, Users, Clock } from 'lucide-react';
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useAddVenue } from "../hooks/useAddVenue";

import "../styles/pages/AddVenue.scss";

const AddVenue = () => {
  const navigate = useNavigate();
  const {
    formData,
    invigilatorList,
    handleChange,
    handleInvigilatorChange,
    handleSubmit
  } = useAddVenue();

  return (
    <div className="dashboard-wrapper">
      <Header />

      <main className="content-area">
        {/* Navigation Tabs */}
        <div className="tab-row">
          <button className="inactive" onClick={() => navigate('/manage-venues')}>
            <Settings size={18} /> Manage Scheduled Exams
          </button>
          <button className="active">
            <PlusCircle size={18} /> Schedule New Exam
          </button>
        </div>

        {/* ONE CONTINUOUS WHITE CONTAINER */}
        <section className="main-card">
          <header>
            <div className="title">
              <PlusCircle size={20} /> 
              <h2>Assign Exam to Venue</h2>
            </div>
          </header>

          <form className="form-body" onSubmit={handleSubmit}>
            
            <div className="form-grid">
              {/* VENUE SECTION */}
              <div className="form-section">
                <h3>Venue Information</h3>
                <div className="input-group">
                  <label>Venue Name</label>
                  <input 
                    type="text" 
                    name="venueName" 
                    placeholder="e.g. Gencor Hall"
                    value={formData.venueName} 
                    onChange={handleChange} 
                  />
                </div>
                <div className="input-group">
                  <label>Seating Capacity</label>
                  <input 
                    type="number" 
                    name="capacity" 
                    placeholder="Max students allowed"
                    value={formData.capacity} 
                    onChange={handleChange} 
                  />
                </div>
              </div>

              {/* EXAM SECTION */}
              <div className="form-section">
                <h3>Exam Schedule</h3>
                <div className="input-group">
                  <label>Module Code & Name</label>
                  <input 
                    type="text" 
                    name="courseCode" 
                    placeholder="e.g. DSO34BT - Development Software III"
                    value={formData.courseCode} 
                    onChange={handleChange} 
                  />
                </div>
                <div className="input-group">
                  <label>Examination Date</label>
                  <input 
                    type="date" 
                    name="date" 
                    value={formData.date} 
                    onChange={handleChange} 
                  />
                </div>
                <div className="row">
                  <div className="input-group">
                    <label>Start Time</label>
                    <input 
                      type="time" 
                      name="startTime" 
                      value={formData.startTime} 
                      onChange={handleChange} 
                    />
                  </div>
                  <div className="input-group">
                    <label>End Time</label>
                    <input 
                      type="time" 
                      name="endTime" 
                      value={formData.endTime} 
                      onChange={handleChange} 
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* INVIGILATORS SECTION */}
            <div className="form-section full-width">
              <h3>Assign Invigilators</h3>
              <div className="invigilators-grid">
                {invigilatorList.map((inv, index) => (
                  <label key={index} className="checkbox-card">
                    <input 
                      type="checkbox" 
                      checked={formData.invigilators.includes(inv)} 
                      onChange={() => handleInvigilatorChange(inv)} 
                    />
                    <span>{inv}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="save-btn">
                <Save size={18} /> Finalize Assignment
              </button>
            </div>
          </form>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default AddVenue;