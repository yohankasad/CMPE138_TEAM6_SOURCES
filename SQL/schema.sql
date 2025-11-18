PRAGMA foreign_keys = ON;

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
    PRIMARY KEY (ssn,name)
);

CREATE TABLE IF NOT EXISTS Doctor(
    id INTEGER NOT NULL,
    license_number TEXT NOT NULL,
    name TEXT NOT NULL,
);

CREATE TABLE IF NOT EXISTS Appointment
(
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT, -- id that needs to increase every time new appointment is placed
    patient_ssn TEXT NOT NULL, -- shown in relationship books
    patient_name TEXT NOT NULL,
    doctor_id INTEGER NOT NULL, -- shown in relationship scheduled with
    scheduled_datetime TEXT NOT NULL, -- attribute datetime

    FOREIGN KEY (patient_ssn,patient_name) 
        REFERENCES Patient(ssn,name)
);
