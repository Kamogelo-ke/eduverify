-- ============================================
-- EduVerify Mock Data for Testing
-- ============================================

-- 1. SYSTEM USERS
-- ============================================
INSERT INTO system_users (Username, Email, FirstName, LastName, Role, PasswordHash, IsActive, CreatedAt) VALUES
('admin', 'admin@edverify.com', 'System', 'Administrator', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmvwXgJqPG', true, NOW()),
('invigilator1', 'john.doe@university.edu', 'John', 'Doe', 'invigilator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmvwXgJqPG', true, NOW()),
('invigilator2', 'jane.smith@university.edu', 'Jane', 'Smith', 'invigilator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmvwXgJqPG', true, NOW()),
('invigilator3', 'mike.johnson@university.edu', 'Mike', 'Johnson', 'invigilator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmvwXgJqPG', true, NOW()),
('tech1', 'sarah.wilson@university.edu', 'Sarah', 'Wilson', 'system', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmvwXgJqPG', true, NOW());

-- 2. VENUES
-- ============================================
INSERT INTO venues (VenueName, Campus, Location, Capacity, Stars, QueueSpeed, IsActive, CreatedAt) VALUES
('Main Exam Hall A', 'Main Campus', 'Building A, Ground Floor', 200, 4.5, 12, true, NOW()),
('Main Exam Hall B', 'Main Campus', 'Building A, First Floor', 150, 4.3, 14, true, NOW()),
('Science Block Auditorium', 'Science Campus', 'Building S, Ground Floor', 100, 4.8, 10, true, NOW()),
('Engineering Hall', 'Engineering Campus', 'Building E, Room 101', 120, 4.2, 15, true, NOW()),
('Business School Center', 'Business Campus', 'Building B, Floor 2', 80, 4.6, 11, true, NOW());

-- 3. STUDENTS
-- ============================================
INSERT INTO students (FirstName, LastName, Email, StudentNumber, AcademicStanding, EnrollmentStatus, ConsentGiven, ConsentDate, CreatedAt) VALUES
-- Computer Science Students
('Alice', 'Johnson', 'alice.j@university.edu', 'CS2024001', 'Good', 'Active', true, NOW(), NOW()),
('Bob', 'Smith', 'bob.smith@university.edu', 'CS2024002', 'Good', 'Active', true, NOW(), NOW()),
('Carol', 'Davis', 'carol.davis@university.edu', 'CS2024003', 'Good', 'Active', true, NOW(), NOW()),
('David', 'Brown', 'david.brown@university.edu', 'CS2024004', 'Probation', 'Active', true, NOW(), NOW()),
('Emma', 'Wilson', 'emma.wilson@university.edu', 'CS2024005', 'Good', 'Active', true, NOW(), NOW()),

-- Engineering Students
('Frank', 'Miller', 'frank.miller@university.edu', 'ENG2024001', 'Good', 'Active', true, NOW(), NOW()),
('Grace', 'Taylor', 'grace.taylor@university.edu', 'ENG2024002', 'Good', 'Active', true, NOW(), NOW()),
('Henry', 'Anderson', 'henry.anderson@university.edu', 'ENG2024003', 'Suspended', 'Active', true, NOW(), NOW()),
('Ivy', 'Thomas', 'ivy.thomas@university.edu', 'ENG2024004', 'Good', 'Active', true, NOW(), NOW()),
('Jack', 'Martinez', 'jack.martinez@university.edu', 'ENG2024005', 'Good', 'Active', true, NOW(), NOW()),

-- Business Students
('Karen', 'White', 'karen.white@university.edu', 'BUS2024001', 'Good', 'Active', true, NOW(), NOW()),
('Leo', 'Harris', 'leo.harris@university.edu', 'BUS2024002', 'Good', 'Active', true, NOW(), NOW()),
('Mona', 'Clark', 'mona.clark@university.edu', 'BUS2024003', 'Probation', 'Active', true, NOW(), NOW()),
('Nick', 'Lewis', 'nick.lewis@university.edu', 'BUS2024004', 'Good', 'Active', true, NOW(), NOW()),
('Olivia', 'Walker', 'olivia.walker@university.edu', 'BUS2024005', 'Good', 'Active', true, NOW(), NOW()),

-- Science Students
('Paul', 'Hall', 'paul.hall@university.edu', 'SCI2024001', 'Good', 'Active', true, NOW(), NOW()),
('Quinn', 'Allen', 'quinn.allen@university.edu', 'SCI2024002', 'Good', 'Active', true, NOW(), NOW()),
('Rachel', 'Young', 'rachel.young@university.edu', 'SCI2024003', 'Good', 'Active', true, NOW(), NOW()),
('Steve', 'King', 'steve.king@university.edu', 'SCI2024004', 'Good', 'Active', true, NOW(), NOW()),
('Tina', 'Wright', 'tina.wright@university.edu', 'SCI2024005', 'Good', 'Active', true, NOW(), NOW()),

-- More students
('Umar', 'Lopez', 'umar.lopez@university.edu', 'CS2024006', 'Good', 'Active', false, NULL, NOW()),
('Vera', 'Hill', 'vera.hill@university.edu', 'CS2024007', 'Good', 'Active', true, NOW(), NOW()),
('Will', 'Scott', 'will.scott@university.edu', 'CS2024008', 'Good', 'Active', true, NOW(), NOW()),
('Xena', 'Green', 'xena.green@university.edu', 'CS2024009', 'Good', 'Active', true, NOW(), NOW()),
('Yusuf', 'Adams', 'yusuf.adams@university.edu', 'CS2024010', 'Good', 'Active', true, NOW(), NOW()),
('Zoe', 'Baker', 'zoe.baker@university.edu', 'CS2024011', 'Good', 'Active', true, NOW(), NOW());

-- 4. EXAM SESSIONS
-- ============================================
INSERT INTO exam_sessions (ModuleCode, ModuleName, VenueLocation, ExamDate, StartTime, EndTime, Status, CreatedBy, MaxCapacity, RegisteredStudents, CreatedAt) VALUES
-- Current/Active Sessions
('SFG117V', 'Introduction to Programming', 'Main Exam Hall A', CURRENT_DATE, '09:00:00', '12:00:00', 'active', 1, 200, 150, NOW()),
('MAT201V', 'Calculus II', 'Main Exam Hall B', CURRENT_DATE, '14:00:00', '17:00:00', 'active', 1, 150, 120, NOW()),
('PHY101V', 'Physics Fundamentals', 'Science Block Auditorium', CURRENT_DATE + 1, '09:00:00', '12:00:00', 'active', 1, 100, 80, NOW()),

-- Upcoming Sessions
('ENG301V', 'Thermodynamics', 'Engineering Hall', CURRENT_DATE + 3, '10:00:00', '13:00:00', 'scheduled', 1, 120, 0, NOW()),
('BUS202V', 'Business Ethics', 'Business School Center', CURRENT_DATE + 5, '13:00:00', '16:00:00', 'scheduled', 1, 80, 0, NOW()),
('CS401V', 'Machine Learning', 'Main Exam Hall A', CURRENT_DATE + 7, '09:00:00', '12:00:00', 'scheduled', 1, 200, 0, NOW()),

-- Past Sessions
('CHE101V', 'Chemistry 101', 'Science Block Auditorium', CURRENT_DATE - 7, '09:00:00', '12:00:00', 'completed', 1, 100, 95, NOW()),
('STA201V', 'Statistics', 'Main Exam Hall B', CURRENT_DATE - 14, '14:00:00', '17:00:00', 'completed', 1, 150, 140, NOW());

-- 5. VERIFICATION LOGS
-- ============================================
INSERT INTO verification_logs (id, id, DeviceID, VerificationOutcome, DigitalSignature, VenueLocation, AttemptNumber, FaceMatchScore, LivenessScore, Timestamp) VALUES
-- Successful verifications
(1, 1, 'CAM_001', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 1, 0.95, 0.92, NOW() - INTERVAL '2 hours'),
(2, 1, 'CAM_001', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 1, 0.87, 0.89, NOW() - INTERVAL '1 hour'),
(3, 1, 'CAM_002', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 1, 0.92, 0.91, NOW() - INTERVAL '30 minutes'),
(4, 1, 'CAM_002', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 2, 0.78, 0.85, NOW() - INTERVAL '15 minutes'),

-- Failed verifications - biometric fail
(5, 1, 'CAM_003', 'Denied_Biometric_Fail', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 1, 0.45, 0.72, NOW() - INTERVAL '1 hour'),
(6, 1, 'CAM_003', 'Denied_Biometric_Fail', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 2, 0.51, 0.68, NOW() - INTERVAL '45 minutes'),
(7, 1, 'CAM_004', 'Denied_Biometric_Fail', 'SIG_' || md5(random()::text), 'Main Exam Hall A', 1, 0.38, 0.71, NOW() - INTERVAL '20 minutes'),

-- Successful in other sessions
(8, 2, 'CAM_005', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall B', 1, 0.94, 0.93, NOW() - INTERVAL '3 hours'),
(9, 2, 'CAM_005', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall B', 1, 0.88, 0.90, NOW() - INTERVAL '2 hours'),
(10, 2, 'CAM_006', 'Success', 'SIG_' || md5(random()::text), 'Main Exam Hall B', 1, 0.91, 0.88, NOW() - INTERVAL '1 hour'),

-- Denied - not registered
(11, 2, 'CAM_006', 'Denied_Not_Registered', 'SIG_' || md5(random()::text), 'Main Exam Hall B', 1, NULL, NULL, NOW() - INTERVAL '30 minutes'),

-- Manual overrides
(12, 3, 'CAM_007', 'Manual_Override', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.65, 0.82, NOW() - INTERVAL '1 hour'),
(13, 3, 'CAM_007', 'Manual_Override', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.60, 0.79, NOW() - INTERVAL '30 minutes'),

-- Past session logs
(1, 7, 'CAM_010', 'Success', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.96, 0.94, CURRENT_DATE - 7 + TIME '09:15:00'),
(2, 7, 'CAM_010', 'Success', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.89, 0.91, CURRENT_DATE - 7 + TIME '09:30:00'),
(3, 7, 'CAM_011', 'Denied_Biometric_Fail', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.42, 0.73, CURRENT_DATE - 7 + TIME '10:00:00'),
(15, 7, 'CAM_011', 'Success', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 2, 0.85, 0.87, CURRENT_DATE - 7 + TIME '10:15:00'),
(16, 7, 'CAM_012', 'Success', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, 0.93, 0.92, CURRENT_DATE - 7 + TIME '10:30:00'),
(17, 7, 'CAM_012', 'Denied_Not_Registered', 'SIG_' || md5(random()::text), 'Science Block Auditorium', 1, NULL, NULL, CURRENT_DATE - 7 + TIME '11:00:00');

-- 6. ACCESS LOGS
-- ============================================
INSERT INTO access_logs (id, id, id, Action, TTSFeedbackSent, Reason, Timestamp) VALUES
-- Grants by system
(1, 1, 1, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '2 hours'),
(1, 2, 1, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '1 hour'),
(1, 3, 1, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '30 minutes'),
(1, 4, 1, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '15 minutes'),

-- Denials
(2, 5, 1, 'deny', 1, 'Face verification failed - low match score', NOW() - INTERVAL '1 hour'),
(2, 6, 1, 'deny', 1, 'Face verification failed - liveness check failed', NOW() - INTERVAL '45 minutes'),
(2, 7, 1, 'deny', 1, 'Face does not match registered student', NOW() - INTERVAL '20 minutes'),

-- Overrides
(2, 12, 3, 'override', 1, 'Student has facial injury - verified with ID', NOW() - INTERVAL '1 hour'),
(3, 13, 3, 'override', 1, 'Camera malfunction - manual verification', NOW() - INTERVAL '30 minutes'),

-- Grants by invigilators
(2, 8, 2, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '3 hours'),
(2, 9, 2, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '2 hours'),
(3, 10, 2, 'grant', 1, 'Face verification successful', NOW() - INTERVAL '1 hour'),
(3, 11, 2, 'deny', 1, 'Not registered for this module', NOW() - INTERVAL '30 minutes');

-- 7. ATTENDANCE REGISTERS
-- ============================================
INSERT INTO attendance_registers (id, id, MarkedBy, id, Status, MarkedAt) VALUES
-- Session 1 attendance
(1, 1, 1, 1, 'present', NOW() - INTERVAL '2 hours'),
(1, 2, 1, 2, 'present', NOW() - INTERVAL '1 hour'),
(1, 3, 1, 3, 'present', NOW() - INTERVAL '30 minutes'),
(1, 4, 1, 4, 'present', NOW() - INTERVAL '15 minutes'),
(1, 5, 2, 5, 'absent', NOW()),
(1, 6, 2, 6, 'absent', NOW()),

-- Session 2 attendance
(2, 8, 2, 8, 'present', NOW() - INTERVAL '3 hours'),
(2, 9, 2, 9, 'present', NOW() - INTERVAL '2 hours'),
(2, 10, 3, 10, 'present', NOW() - INTERVAL '1 hour'),
(2, 11, 3, 11, 'absent', NOW()),

-- Session 3 attendance
(3, 12, 2, 12, 'present', NOW() - INTERVAL '1 hour'),
(3, 13, 3, 13, 'present', NOW() - INTERVAL '30 minutes'),

-- Past session attendance
(7, 1, 1, 14, 'present', CURRENT_DATE - 7 + TIME '09:15:00'),
(7, 2, 1, 15, 'present', CURRENT_DATE - 7 + TIME '09:30:00'),
(7, 3, 1, 16, 'absent', CURRENT_DATE - 7 + TIME '09:30:00'),
(7, 15, 2, 17, 'present', CURRENT_DATE - 7 + TIME '10:15:00'),
(7, 16, 2, 18, 'present', CURRENT_DATE - 7 + TIME '10:30:00'),
(7, 17, 2, 19, 'absent', CURRENT_DATE - 7 + TIME '10:30:00');

-- 8. AI METRICS
-- ============================================
INSERT INTO ai_metrics (id, FAR, FRR, AvgProcessTime, TotalProcessed, YOLOv8_Accuracy, ArcFace_MatchingTime, DINOv2_LivenessAccuracy, GPU_Utilization, Timestamp) VALUES
(1, 0.023, 0.045, 12.5, 150, 0.96, 8.2, 0.94, 45.5, NOW()),
(2, 0.018, 0.038, 11.8, 120, 0.97, 7.9, 0.95, 42.3, NOW()),
(3, 0.031, 0.052, 13.2, 80, 0.95, 8.5, 0.93, 48.1, NOW()),
(7, 0.025, 0.048, 12.9, 95, 0.96, 8.1, 0.94, 44.7, CURRENT_DATE - 7);

-- 9. MANUAL OVERRIDES TABLE (if exists)
-- ============================================
-- Note: This table might not exist in your schema yet
CREATE TABLE IF NOT EXISTS manual_overrides (
    OverrideID SERIAL PRIMARY KEY,
    LogID INTEGER REFERENCES verification_logs(LogID),
    InvigilatorID INTEGER REFERENCES system_users(id),
    OverrideReason VARCHAR(500),
    Timestamp TIMESTAMP DEFAULT NOW()
);

INSERT INTO manual_overrides (LogID, InvigilatorID, OverrideReason, Timestamp) VALUES
(12, 2, 'Student has facial injury - verified with student ID card', NOW() - INTERVAL '1 hour'),
(13, 3, 'Camera malfunction - manual verification by invigilator', NOW() - INTERVAL '30 minutes');