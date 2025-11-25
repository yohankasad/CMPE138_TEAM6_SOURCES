--   SJSU CMPE 138 FALL 2025 TEAM6 

PRAGMA foreign_keys = ON ;

INSERT INTO Department(name,   head_doctor_id)
VALUES
('Cardiology', NULL),
('Neurology' ,NULL),
   ('Pediatrics' ,  NULL)
;



INSERT INTO Doctor ( id , license_number , name , department_name )
VALUES
 (1,'LIC1001','Dr. Alice Heart','Cardiology'),
 (2, 'LIC1002','Dr. Brian Nerves' , 'Neurology'),
(3,'LIC1003' , 'Dr. Carol Kids','Pediatrics'),
 (4,'LIC1004','Dr. Daniel Carter' ,   'Cardiology')
;



INSERT INTO Primary_Care(primary_care_id)
VALUES
(1),   -- Alice
(3)    -- Carol
;



INSERT INTO Specialist( specialist_doctor_id , specialization )
VALUES
(2,'Neurology'),
   (4,'Interventional Cardiology')
;


UPDATE Department
   SET head_doctor_id = 1
 WHERE name='Cardiology';

UPDATE Department SET head_doctor_id=2 WHERE name = 'Neurology'  ;
UPDATE Department
SET head_doctor_id = 3
WHERE name='Pediatrics';



INSERT INTO Healthcare_Insurance ( policy_id , Company )
VALUES
(1,'Blue Shield'),
 (2,'Kaiser Permanente') ,
(3 , 'United Health')
;


INSERT INTO Patient(
 ssn, name, age, weight, phone_number,
 dob_day, dob_month, dob_year,
 street, city, state, zip_code,
 primary_care_assigned_id
)
VALUES
('111-22-3333','John Doe',35,80.5,'408-555-1000',
 15,5,1990,'123 Main St','San Jose','CA','95112',1),

('222-33-4444','Jane Smith',29,62.3,'408-555-2000',
 3,11,1995,'456 Oak Ave','San Jose','CA','95113',3),


('333-44-5555','Michael Brown',42,90.0,'408-555-3000',
22,1,1983,'789 Pine Rd','Santa Clara','CA','95050',1),

('444-55-6666','Emily Davis',8,28.0,'408-555-4000',
9,7,2017,'321 Maple Dr','Santa Clara','CA','95051',3)
;



INSERT INTO Patient_Healthcare_Insurance
( patient_ssn , patient_name , policy_id )
VALUES
 ('111-22-3333','John Doe',1),
('111-22-3333','John Doe',2),
('222-33-4444','Jane Smith',2),
('333-44-5555','Michael Brown',1),
('444-55-6666','Emily Davis',3)
;



INSERT INTO Appointment(
 appointment_id,
 patient_ssn , patient_name ,
 doctor_id ,
 scheduled_datetime
)
VALUES
(1,'111-22-3333','John Doe',1,'2025-04-01 09:00:00'),
 (2,'222-33-4444','Jane Smith',2,'2025-04-02 10:30:00'),
(3,'333-44-5555','Michael Brown',1,'2025-04-03 11:15:00'),
 (4,'444-55-6666','Emily Davis',3,'2025-04-04 14:00:00')
;



INSERT INTO Pharmacy(street,city,state,zip_code,telephone)
VALUES
('10 Health St','San Jose','CA','95112','408-777-1000'),
('500 Wellness Ave','Santa Clara','CA','95050','408-777-2000')
;



INSERT INTO Pharmacist(
 id, name,
 pharmacy_street, pharmacy_city, pharmacy_state, pharmacy_zip_code
)
VALUES
(1,'Alice Pharmacist',
 '10 Health St','San Jose','CA','95112'),
(2,'Bob Pharmacist',
 '500 Wellness Ave','Santa Clara','CA','95050')
;


INSERT INTO Dispenser(dispenser_id)
VALUES (1),
 (2)
;


INSERT INTO Inventory_manager ( inventory_manager_id )
VALUES
(2)
;



INSERT INTO Medication(name, quantity_ordered , quantity_in_stock , location)
VALUES
('Atorvastatin',150,200,'Shelf A1'),
('Lisinopril',220,300,'Shelf A2'),
   ('Amoxicillin',80,150,'Fridge F1')
;


INSERT INTO Manages( inventory_manager_id , medication_name )
VALUES
(2,'Atorvastatin'),
(2,'Lisinopril'),
(2,'Amoxicillin')
;



INSERT INTO Prescription(
 prescription_id,
 prescriber_id,
 policy_id,
 prescripted_patient_ssn,
 prescripted_patient_name,
 dosage
)
VALUES
(1,1,1,'111-22-3333','John Doe','Atorvastatin 20mg once daily'),
(2,2,2,'222-33-4444','Jane Smith','Lisinopril 10mg once daily'),
(3,3,3,'444-55-6666','Emily Davis','Amoxicillin 250mg twice daily')
;



INSERT INTO Medication_dispensed( prescription_id , dispenser_id )
VALUES
(1,1),
(2,1),
(3,2)
;



INSERT INTO Contains( prescription_id , medication_name )
VALUES
(1,'Atorvastatin'),
(2,'Lisinopril'),
(3,'Amoxicillin')
;

-- Just An Admin user 
INSERT INTO User_Account (username, password_hash, role)
VALUES (
    'admin',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', -- admin123
    'admin'
);

-- Doctor Alice Heart 1
INSERT INTO User_Account (username, password_hash, role, doctor_id)
VALUES (
    'dralice',
    'c3362e4da49c24d379b72152ae6c99f1fa035f52829dceed715a7bf8bb464b98', -- doc123
    'doctor',
    1
);

-- Patient  John Doe (SSN 111-22-3333)
INSERT INTO User_Account (username, password_hash, role, patient_ssn, patient_name)
VALUES (
    'johndoe',
    'd4587ea9ead060c13fd994f21ecfa7926272a78854a2c20136b10a3c9e53e71e', -- patient123
    'patient',
    '111-22-3333',
    'John Doe'
);

-- Pharmacist Alice Pharmacist 1
INSERT INTO User_Account (username, password_hash, role, pharmacist_id)
VALUES (
    'alicepharm',
    '47a0df34426c6c34a4ee69b75e8a5c31872cddc43df8fbe5d84a020ca5a3c623', -- pharm123
    'pharmacist',
    1
);
