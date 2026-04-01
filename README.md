# EduVerify

## Project Overview

At Tshwane University of Technology, verifying whether students qualify to write exams and confirming their identity is currently done manually. This process is slow, prone to errors, and creates long queues. Some students may even impersonate others, compromising the fairness and security of examinations.

**Proposed Solution:**  
EduVerify is an AI-driven system that automates exam verification. Using real-time face recognition and liveness detection, the system verifies student identities at exam venues and checks their eligibility by querying the university database for predicate marks. Students receive instant feedback via AI-assisted text-to-speech, while invigilators can override failed recognition attempts. This solution reduces queues, prevents cheating, and ensures exams are fair and organized.

**Project Objectives (SMART):**
- **Specific:** Real-time student feedback, web-based platform accessible on all legal browsers, face recognition for identity verification, exam eligibility checks, restricted access for unauthorized students, speed up check-in, invigilator override option.
- **Measurable:** Face recognition accuracy over 90%, remove impersonation, use React for frontend and Python for backend.
- **Achievable:** Core functionality to be fully implemented and tested by May 2026.
- **Relevant:** Supports academic events by improving fairness, security, and efficiency during exams.
- **Time-bound:** Implementation within the semester with defined deliverables.

**Scope:**
- **Included:** Facial recognition, integration with TUT database, real-time feedback via AI-assisted text-to-speech, monitoring and registering students’ faces, secure handling of student data.
- **Excluded:** Non-examination student activities, full student information post recognition, biometrics other than face recognition.

**Expected Deliverables:**
- Fully functional facial recognition at exam venues.
- Integration with academic predicate database for eligibility checks.
- AI-assisted real-time voice feedback: "Access Granted" / "Access Denied".
- Web-based interface for students and invigilators.
  
## Technologies Used

- **Frontend:** React  
- **Backend:** Python 3.10, FastAPI  
- **Database:** PostgreSQL  
- **AI Models:** Hugging Face Hub for face recognition and liveness detection  
- **Security:** AES-256 Encryption  
- **Deployment:** Docker  

This combination of technologies ensures a fast, secure, and scalable system capable of automating exam verification efficiently and accurately.
