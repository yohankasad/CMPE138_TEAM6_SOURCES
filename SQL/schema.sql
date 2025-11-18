PRAGMA foreign_keys = ON;

CREATE TABLE Department(
    name TEXT PRIMARY KEY,
    head_doctor_id INTEGER UNIQUE,
    FOREIGN KEY (head_doctor_id) -- head of department relationship
        REFERENCES Doctor(id)
);

CREATE TABLE IF NOT EXISTS Doctor(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_number TEXT NOT NULL,
    name TEXT NOT NULL,
    department_name TEXT NOT NULL, -- belongs to relationship
    FOREIGN KEY (department_name)
        REFERENCES Department(name)
);

CREATE TABLE Primary_Care(
    primary_care_id INTEGER PRIMARY KEY,

    FOREIGN KEY (primary_care_id) 
        REFERENCES Doctor(id)
);

CREATE TABLE Specialist(
    specialist_doctor_id INTEGER PRIMARY KEY,
    specialization TEXT NOT NULL,
    FOREIGN KEY (specialist_doctor_id)
        REFERENCES Doctor(id)
);

CREATE TABLE Healthcare_Insurance(
    policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Company TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Patient(
    ssn TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    weight REAL,
    phone_number TEXT,
    dob_day INTEGER CHECK (dob_day >= 1 AND dob_day <= 31), 
    dob_month INTEGER CHECK (dob_month >= 1 AND dob_month <= 12),
    dob_year INTEGER,
    street TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    primary_care_assigned_id INTEGER, -- assigned to relationship

    PRIMARY KEY (ssn,name),
    FOREIGN KEY (primary_care_assigned_id) 
        REFERENCES Primary_Care(primary_care_id)
);

CREATE TABLE IF NOT EXISTS Appointment
(
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT, -- id that needs to increase every time new appointment is placed
    patient_ssn TEXT NOT NULL, -- shown in relationship books
    patient_name TEXT NOT NULL,
    doctor_id INTEGER NOT NULL, -- shown in relationship scheduled with
    scheduled_datetime TEXT NOT NULL, -- 

    FOREIGN KEY (patient_ssn,patient_name) 
        REFERENCES Patient(ssn,name),
    FOREIGN KEY (doctor_id) 
        REFERENCES Doctor(id)
);

CREATE TABLE Patient_Healthcare_Insurance(
    patient_ssn TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    policy_id INTEGER NOT NULL,
    PRIMARY KEY (patient_ssn, patient_name, policy_id),
    FOREIGN KEY (patient_ssn, patient_name)
        REFERENCES Patient(ssn, name),
    FOREIGN KEY (policy_id)
        REFERENCES Healthcare_Insurance(policy_id)
);

CREATE TABLE Prescription (
    prescription_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    prescriber_id INTEGER NOT NULL, -- prescribes relationship 
    policy_id INTEGER NOT NULL,    -- this one seems weird on the paid by relation side. Our er diagram doesnt match this as 1 to m basically would have foreign attribute on m side
    prescripted_patient_ssn TEXT NOT NULL,
    prescripted_patient_name TEXT NOT NULL, -- assigned to relationship

    dosage TEXT NOT NULL,           

    FOREIGN KEY (prescriber_id)
        REFERENCES Doctor(id),
    FOREIGN KEY (policy_id)
        REFERENCES Healthcare_Insurance(policy_id),
    FOREIGN KEY (prescripted_patient_ssn,prescripted_patient_name)
        REFERENCES Patient(ssn,name)
);

CREATE TABLE Pharmacy(
    street TEXT NOT NULL, -- changed from address to full values
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    telephone TEXT NOT NULL,

    PRIMARY KEY (street, city, state, zip_code)
);

CREATE TABLE Pharmacist(
    id INTEGER PRIMARY KEY, -- changes from license number
    name TEXT NOT NULL,
    pharmacy_street TEXT NOT NULL,
    pharmacy_city TEXT NOT NULL,
    pharmacy_state TEXT NOT NULL,
    pharmacy_zip_code TEXT NOT NULL,

    FOREIGN KEY(pharmacy_street,pharmacy_city,pharmacy_state,pharmacy_zip_code)
        REFERENCES Pharmacy(street,city,state,zip_code)
);

CREATE TABLE Dispenser(
    dispenser_id INTEGER PRIMARY KEY,

    FOREIGN KEY (dispenser_id)
        REFERENCES Pharmacist(id)
);

CREATE TABLE Inventory_manager(
    inventory_manager_id INTEGER PRIMARY KEY,

    FOREIGN KEY (inventory_manager_id)
        REFERENCES Pharmacist(id)
);

CREATE TABLE Medication_dispensed(
    prescription_id INTEGER NOT NULL, -- dispensed by relationship
    dispenser_id INTEGER NOT NULL,

    PRIMARY KEY(prescription_id,dispenser_id),

    FOREIGN KEY (prescription_id)
        REFERENCES Prescription(prescription_id),
    FOREIGN KEY (dispenser_id)
        REFERENCES Dispenser(dispenser_id)
);

CREATE TABLE Medication(
    name               TEXT PRIMARY KEY,
    quantity_ordered   INTEGER NOT NULL,
    quantity_in_stock  INTEGER NOT NULL,
    location           TEXT,
    
    CHECK (quantity_in_stock > 0),
    CHECK (quantity_ordered > 0),
    CHECK (quantity_ordered < quantity_in_stock)
);

CREATE TABLE Manages(
    inventory_manager_id INTEGER NOT NULL, -- manages relationship
    medication_name TEXT NOT NULL,
    PRIMARY KEY(inventory_manager_id,medication_name),

    FOREIGN KEY (inventory_manager_id)
        REFERENCES Inventory_manager(inventory_manager_id),
    FOREIGN KEY (medication_name)
        REFERENCES Medication(name)
);

CREATE TABLE Contains(
    prescription_id INTEGER NOT NULL,
    medication_name TEXT NOT NULL,

    PRIMARY KEY (prescription_id,medication_name), -- contains relatiopnship

    FOREIGN KEY (prescription_id)
        REFERENCES Prescription(prescription_id),
    FOREIGN KEY (medication_name)
        REFERENCES Medication(name)
);

CREATE TABLE IF NOT EXISTS User_Account (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('patient','doctor','pharmacist','admin')),

    patient_ssn    TEXT,
    patient_name   TEXT,
    doctor_id      INTEGER,
    pharmacist_id  INTEGER,

    FOREIGN KEY (patient_ssn, patient_name)
        REFERENCES Patient(ssn, name),
    FOREIGN KEY (doctor_id)
        REFERENCES Doctor(id),
    FOREIGN KEY (pharmacist_id)
        REFERENCES Pharmacist(id)
);
