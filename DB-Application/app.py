import sqlite3
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "SQL"
DB_PATH = SQL_DIR / "schema.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(plain: str) -> str:
    """Return SHA-256 hash of password."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def get_user_by_username(conn, username):
    q = "SELECT * FROM User_Account WHERE username = ?;"
    return conn.execute(q, (username,)).fetchone()


def register_user(conn):
    print("\n--- Register New User ---")
    username = input("Choose username: ").strip()

    existing = get_user_by_username(conn, username)
    if existing:
        print("That username already exists.\n")
        return

    pwd = input("Choose password: ").strip()
    confirm = input("Confirm password: ").strip()
    if pwd != confirm:
        print("Passwords do not match.\n")
        return

    print("Available roles: patient / doctor / pharmacist / admin")
    role = input("Choose role: ").strip().lower()

    if role not in ("patient", "doctor", "pharmacist", "admin"):
        print("Invalid role.\n")
        return

    # Default values for foreign links
    patient_ssn = None
    patient_name = None
    doctor_id = None
    pharmacist_id = None

    # Validate role links
    if role == "patient":
        patient_ssn = input("Patient SSN (must exist): ").strip()
        patient_name = input("Patient Name (exact match): ").strip()

        row = conn.execute(
            "SELECT 1 FROM Patient WHERE ssn = ? AND name = ?;",
            (patient_ssn, patient_name)
        ).fetchone()

        if not row:
            print("No such patient exists.\n")
            return

    elif role == "doctor":
        doctor_id = input("Doctor ID (must exist): ").strip()
        row = conn.execute("SELECT 1 FROM Doctor WHERE id = ?;", (doctor_id,)).fetchone()
        if not row:
            print("No such doctor.\n")
            return

    elif role == "pharmacist":
        pharmacist_id = input("Pharmacist ID (must exist): ").strip()
        row = conn.execute("SELECT 1 FROM Pharmacist WHERE id = ?;", (pharmacist_id,)).fetchone()
        if not row:
            print("No such pharmacist.\n")
            return

    pwd_hash = hash_password(pwd)

    conn.execute("""
        INSERT INTO User_Account 
        (username, password_hash, role, patient_ssn, patient_name, doctor_id, pharmacist_id)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (username, pwd_hash, role, patient_ssn, patient_name, doctor_id, pharmacist_id))
    conn.commit()

    print(f"User '{username}' registered as '{role}'.\n")


def login(conn):
    print("\n=== Login ===")

    for _ in range(3):  # up to 3 failed attempts
        username = input("Username: ").strip()
        pwd = input("Password: ").strip()

        user = get_user_by_username(conn, username)

        if not user:
            print("Invalid username or password.\n")
            continue

        if hash_password(pwd) != user["password_hash"]:
            print("Invalid username or password.\n")
            continue

        print(f"\nWelcome back, {username}! Role = {user['role']}\n")
        return user

    print("Too many failed attempts.\n")
    return None

def run_role_menu(conn, user):
    role = user["role"]

    if role == "admin":
        admin_menu(conn, user)
    elif role == "doctor":
        doctor_menu(conn, user)
    elif role == "patient":
        patient_menu(conn, user)
    elif role == "pharmacist":
        pharmacist_menu(conn, user)
    else:
        print("Unknown role. Contact admin.\n")


#   MENU LOOP
def admin_menu(conn, user):
    while True:
        print(f"""
==== ADMIN MENU (Logged in as {user['username']}) ====
1. List Patients
2. List Appointments
3. Create Appointment
4. View Patient Prescriptions
5. View Medication Inventory
6. List Doctors
7. List Departments
8. View Department Details
9. Create Department
10. View Specialist Doctors
11. View Primary Care Doctors
12. List Pharmacies
13. View Pharmacy Details
14. Create Pharmacy
15. View Pharmacist Details
16. View Prescription Medications
17. Add Medication to Prescription
18. Remove Medication from Prescription
19. Assign Primary Care Doctor to Patient
20. View Patient's Primary Care Doctor
21. Register New User
22. System Statistics
0. Logout
""")
        choice = input("Select an option: ").strip()

        if choice == "1":
            list_patients(conn)
        elif choice == "2":
            list_appointments(conn)
        elif choice == "3":
            create_appointment(conn)
        elif choice == "4":
            list_prescriptions_for_patient(conn)
        elif choice == "5":
            list_medications(conn)
        elif choice == "6":
            list_doctors(conn)
        elif choice == "7":
            list_departments(conn)
        elif choice == "8":
            view_department_details(conn)
        elif choice == "9":
            create_department(conn)
        elif choice == "10":
            view_specialist_doctors(conn)
        elif choice == "11":
            view_primary_care_doctors(conn)
        elif choice == "12":
            list_pharmacies(conn)
        elif choice == "13":
            view_pharmacy_details(conn)
        elif choice == "14":
            create_pharmacy(conn)
        elif choice == "15":
            view_pharmacist_details(conn)
        elif choice == "16":
            view_prescription_medications(conn)
        elif choice == "17":
            add_medication_to_prescription(conn)
        elif choice == "18":
            remove_medication_from_prescription(conn)
        elif choice == "19":
            assign_primary_care_doctor(conn)
        elif choice == "20":
            view_assigned_primary_care(conn)
        elif choice == "21":
            register_user(conn)
        elif choice == "22":
            view_system_statistics(conn)
        elif choice == "0":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice.\n")


def doctor_menu(conn, user):
    doctor_id = user["doctor_id"]

    while True:
        print(f"""
==== DOCTOR MENU (Dr. {user['username']}) ====
1. View My Appointments
2. Create Prescription
3. View Prescriptions I Issued
0. Logout
""")

        choice = input("Select an option: ").strip()

        if choice == "1":
            view_doctor_appointments(conn, doctor_id)

        elif choice == "2":
            create_prescription(conn, doctor_id)

        elif choice == "3":
            view_prescriptions_by_doctor(conn, doctor_id)

        elif choice == "0":
            print("Logging out...\n")
            break

        else:
            print("Invalid choice.\n")
#Doc Appointment
def view_doctor_appointments(conn, doctor_id):
    print("\n--- My Appointments ---")
    q = """
        SELECT A.appointment_id, A.scheduled_datetime,
               P.name AS patient_name
        FROM Appointment A
        JOIN Patient P ON A.patient_ssn = P.ssn
        WHERE A.doctor_id = ?
        ORDER BY A.scheduled_datetime;
    """
    rows = conn.execute(q, (doctor_id,)).fetchall()

    if not rows:
        print("No appointments found.\n")
        return

    for r in rows:
        print(f"{r['appointment_id']} | {r['scheduled_datetime']} | {r['patient_name']}")
    print()

#create prescription

def create_prescription(conn, doctor_id):
    print("\n--- Create Prescription ---")
    patient_ssn = input("Patient SSN: ").strip()
    patient_name = conn.execute("SELECT name FROM Patient WHERE ssn = ?", (patient_ssn,)).fetchone()

    if not patient_name:
        print("No such patient.\n")
        return

    dosage = input("Dosage Instructions: ").strip()

    conn.execute("""
        INSERT INTO Prescription (prescriber_id, prescripted_patient_ssn, prescripted_patient_name, dosage)
        VALUES (?, ?, ?, ?);
    """, (doctor_id, patient_ssn, patient_name["name"], dosage))

    conn.commit()
    print("Prescription created.\n")

#view precscription

def view_prescriptions_by_doctor(conn, doctor_id):
    print("\n--- Prescriptions I Issued ---")

    q = """
        SELECT prescription_id, prescripted_patient_name, dosage
        FROM Prescription
        WHERE prescriber_id = ?
        ORDER BY prescription_id DESC;
    """

    rows = conn.execute(q, (doctor_id,)).fetchall()

    if not rows:
        print("No prescriptions issued.\n")
        return

    for r in rows:
        print(f"{r['prescription_id']} | {r['prescripted_patient_name']} | {r['dosage']}")
    print()


def patient_menu(conn, user):
    patient_ssn = user["patient_ssn"]
    patient_name = user["patient_name"]

    while True:
        print(f"""
==== PATIENT MENU (Logged in as {user['username']}) ====
1. View My Personal Information
2. View My Appointments
3. View My Prescriptions
4. View Available Doctors
5. View My Insurance Information
6. View My Primary Care Doctor
7. View Medications in Prescription
8. Request New Appointment
9. View Appointment History
0. Logout
""")

        choice = input("Select an option: ").strip()

        if choice == "1":
            view_patient_info(conn, patient_ssn, patient_name)

        elif choice == "2":
            view_patient_appointments(conn, patient_ssn, patient_name)

        elif choice == "3":
            view_patient_prescriptions(conn, patient_ssn, patient_name)

        elif choice == "4":
            list_doctors(conn)

        elif choice == "5":
            view_patient_insurance(conn, patient_ssn, patient_name)

        elif choice == "6":
            view_assigned_primary_care_for_patient(conn, patient_ssn, patient_name)

        elif choice == "7":
            view_prescription_medications_patient(conn, patient_ssn, patient_name)

        elif choice == "8":
            request_appointment(conn, patient_ssn, patient_name)

        elif choice == "9":
            view_appointment_history(conn, patient_ssn, patient_name)

        elif choice == "0":
            print("Logging out...\n")
            break

        else:
            print("Invalid choice.\n")


#   PATIENT OPERATIONS
def view_patient_info(conn, patient_ssn, patient_name):
    print("\n--- My Personal Information ---")
    
    q = """
        SELECT ssn, name, age, weight, phone_number, 
               dob_day, dob_month, dob_year, 
               street, city, state, zip_code
        FROM Patient
        WHERE ssn = ? AND name = ?;
    """
    
    row = conn.execute(q, (patient_ssn, patient_name)).fetchone()
    
    if not row:
        print("Patient record not found.\n")
        return
    
    print(f"SSN: {row['ssn']}")
    print(f"Name: {row['name']}")
    print(f"Age: {row['age']}")
    print(f"Weight: {row['weight']} lbs")
    print(f"Phone: {row['phone_number']}")
    
    if row['dob_day'] and row['dob_month'] and row['dob_year']:
        print(f"Date of Birth: {row['dob_month']}/{row['dob_day']}/{row['dob_year']}")
    
    if row['street'] or row['city'] or row['state']:
        address = f"{row['street']}, {row['city']}, {row['state']} {row['zip_code']}"
        print(f"Address: {address}")
    
    print()


def view_patient_appointments(conn, patient_ssn, patient_name):
    print("\n--- My Appointments ---")
    
    q = """
        SELECT A.appointment_id, A.scheduled_datetime, D.name AS doctor_name, D.department_name
        FROM Appointment A
        JOIN Doctor D ON A.doctor_id = D.id
        WHERE A.patient_ssn = ? AND A.patient_name = ?
        ORDER BY A.scheduled_datetime;
    """
    
    rows = conn.execute(q, (patient_ssn, patient_name)).fetchall()
    
    if not rows:
        print("No appointments scheduled.\n")
        return
    
    print(f"{'ID':<5} | {'Date & Time':<20} | {'Doctor':<20} | {'Department':<15}")
    print("-" * 65)
    for r in rows:
        print(f"{r['appointment_id']:<5} | {r['scheduled_datetime']:<20} | {r['doctor_name']:<20} | {r['department_name']:<15}")
    print()


def view_patient_prescriptions(conn, patient_ssn, patient_name):
    print("\n--- My Prescriptions ---")
    
    q = """
        SELECT Pr.prescription_id, D.name AS prescriber_name, Pr.dosage
        FROM Prescription Pr
        JOIN Doctor D ON Pr.prescriber_id = D.id
        WHERE Pr.prescripted_patient_ssn = ? AND Pr.prescripted_patient_name = ?
        ORDER BY Pr.prescription_id DESC;
    """
    
    rows = conn.execute(q, (patient_ssn, patient_name)).fetchall()
    
    if not rows:
        print("No prescriptions found.\n")
        return
    
    print(f"{'Rx ID':<8} | {'Prescriber':<20} | {'Dosage':<40}")
    print("-" * 70)
    for r in rows:
        print(f"{r['prescription_id']:<8} | {r['prescriber_name']:<20} | {r['dosage']:<40}")
    print()


def view_patient_insurance(conn, patient_ssn, patient_name):
    print("\n--- My Insurance Information ---")
    
    q = """
        SELECT phi.policy_id, hi.Company
        FROM Patient_Healthcare_Insurance phi
        JOIN Healthcare_Insurance hi ON phi.policy_id = hi.policy_id
        WHERE phi.patient_ssn = ? AND phi.patient_name = ?;
    """
    
    rows = conn.execute(q, (patient_ssn, patient_name)).fetchall()
    
    if not rows:
        print("No insurance policies found.\n")
        return
    
    print(f"{'Policy ID':<12} | {'Insurance Company':<30}")
    print("-" * 45)
    for r in rows:
        print(f"{r['policy_id']:<12} | {r['Company']:<30}")
    print()


def view_assigned_primary_care_for_patient(conn, patient_ssn, patient_name):
    print("\n--- My Primary Care Doctor ---")
    
    q = """
        SELECT P.ssn, P.name, D.name AS doctor_name, D.department_name
        FROM Patient P
        LEFT JOIN Primary_Care PC ON P.primary_care_assigned_id = PC.primary_care_id
        LEFT JOIN Doctor D ON PC.primary_care_id = D.id
        WHERE P.ssn = ? AND P.name = ?;
    """
    
    row = conn.execute(q, (patient_ssn, patient_name)).fetchone()
    
    if not row:
        print("Patient information not found.\n")
        return
    
    if row['doctor_name']:
        print(f"Primary Care Doctor: {row['doctor_name']} (Department: {row['department_name']})")
    else:
        print("Primary Care Doctor: Not assigned")
    print()


def view_prescription_medications_patient(conn, patient_ssn, patient_name):
    print("\n--- View Medications in Your Prescriptions ---")
    
    prescription_id = input("Enter prescription ID: ").strip()
    
    # Verify this prescription belongs to the patient
    q_verify = """
        SELECT * FROM Prescription
        WHERE prescription_id = ? AND prescripted_patient_ssn = ? AND prescripted_patient_name = ?;
    """
    
    if not conn.execute(q_verify, (prescription_id, patient_ssn, patient_name)).fetchone():
        print("Prescription not found or does not belong to you.\n")
        return
    
    q = """
        SELECT C.medication_name, M.quantity_in_stock, M.location
        FROM Contains C
        JOIN Medication M ON C.medication_name = M.name
        WHERE C.prescription_id = ?
        ORDER BY C.medication_name;
    """
    
    rows = conn.execute(q, (prescription_id,)).fetchall()
    
    if not rows:
        print(f"No medications linked to prescription {prescription_id}.\n")
        return
    
    print(f"\nMedications in Prescription {prescription_id}:")
    print(f"{'Medication':<30} | {'Stock':<10} | {'Location':<20}")
    print("-" * 65)
    for r in rows:
        print(f"{r['medication_name']:<30} | {r['quantity_in_stock']:<10} | {r['location']:<20}")
    print()


def request_appointment(conn, patient_ssn, patient_name):
    print("\n--- Request New Appointment ---")
    
    # Show available doctors
    print("Available Doctors:")
    doctors = conn.execute("""
        SELECT id, name, department_name FROM Doctor ORDER BY name;
    """).fetchall()
    
    if not doctors:
        print("No doctors available.\n")
        return
    
    for doc in doctors:
        print(f"ID: {doc['id']} | {doc['name']} ({doc['department_name']})")
    
    doctor_id = input("\nEnter doctor ID: ").strip()
    
    # Verify doctor exists
    q_check = "SELECT * FROM Doctor WHERE id = ?;"
    if not conn.execute(q_check, (doctor_id,)).fetchone():
        print("Invalid doctor ID.\n")
        return
    
    scheduled_datetime = input("Enter appointment date/time (YYYY-MM-DD HH:MM:SS): ").strip()
    
    try:
        conn.execute("""
            INSERT INTO Appointment (patient_ssn, patient_name, doctor_id, scheduled_datetime)
            VALUES (?, ?, ?, ?);
        """, (patient_ssn, patient_name, doctor_id, scheduled_datetime))
        conn.commit()
        print("Appointment requested successfully.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error requesting appointment: {e}\n")


def view_appointment_history(conn, patient_ssn, patient_name):
    print("\n--- Appointment History ---")
    
    q = """
        SELECT A.appointment_id, A.scheduled_datetime, D.name AS doctor_name, D.department_name
        FROM Appointment A
        JOIN Doctor D ON A.doctor_id = D.id
        WHERE A.patient_ssn = ? AND A.patient_name = ?
        ORDER BY A.scheduled_datetime DESC;
    """
    
    rows = conn.execute(q, (patient_ssn, patient_name)).fetchall()
    
    if not rows:
        print("No appointment history.\n")
        return
    
    print(f"{'ID':<5} | {'Date & Time':<20} | {'Doctor':<20} | {'Department':<15}")
    print("-" * 65)
    for r in rows:
        print(f"{r['appointment_id']:<5} | {r['scheduled_datetime']:<20} | {r['doctor_name']:<20} | {r['department_name']:<15}")
    print()


def pharmacist_menu(conn, user):
    pharmacist_id = user["pharmacist_id"]

    while True:
        print(f"""
==== PHARMACIST MENU (Logged in as {user['username']}) ====
1. View Available Medications
2. View Pending Prescriptions
3. Dispense a Prescription
4. View Medication Inventory
5. Update Medication Stock
0. Logout
""")

        choice = input("Select an option: ").strip()

        if choice == "1":
            list_medications(conn)

        elif choice == "2":
            view_pending_prescriptions(conn)

        elif choice == "3":
            dispense_prescription(conn, pharmacist_id)

        elif choice == "4":
            view_medication_inventory(conn)

        elif choice == "5":
            update_medication_stock(conn)

        elif choice == "0":
            print("Logging out...\n")
            break

        else:
            print("Invalid choice.\n")


#   PHARMACIST OPERATIONS
def view_pending_prescriptions(conn):
    print("\n--- Pending Prescriptions ---")

    q = """
        SELECT Pr.prescription_id, P.name AS patient_name, P.ssn AS patient_ssn,
               D.name AS doctor_name, Pr.dosage
        FROM Prescription Pr
        JOIN Patient P ON Pr.prescripted_patient_ssn = P.ssn AND Pr.prescripted_patient_name = P.name
        JOIN Doctor D ON Pr.prescriber_id = D.id
        WHERE Pr.prescription_id NOT IN (SELECT prescription_id FROM Medication_dispensed)
        ORDER BY Pr.prescription_id;
    """

    rows = conn.execute(q).fetchall()

    if not rows:
        print("No pending prescriptions.\n")
        return

    print(f"{'Rx ID':<8} | {'Patient Name':<20} | {'Patient SSN':<12} | {'Doctor':<15} | {'Dosage':<30}")
    print("-" * 95)
    for r in rows:
        print(f"{r['prescription_id']:<8} | {r['patient_name']:<20} | {r['patient_ssn']:<12} | {r['doctor_name']:<15} | {r['dosage']:<30}")
    print()


def dispense_prescription(conn, pharmacist_id):
    print("\n--- Dispense Prescription ---")

    prescription_id = input("Enter prescription ID to dispense: ").strip()

    # Check if prescription exists and is not already dispensed
    q = "SELECT * FROM Prescription WHERE prescription_id = ?"
    rx = conn.execute(q, (prescription_id,)).fetchone()

    if not rx:
        print("Prescription not found.\n")
        return

    # Check if already dispensed
    q = "SELECT * FROM Medication_dispensed WHERE prescription_id = ?"
    if conn.execute(q, (prescription_id,)).fetchone():
        print("This prescription has already been dispensed.\n")
        return

    # Check if pharmacist exists as a dispenser
    q = "SELECT * FROM Dispenser WHERE dispenser_id = ?"
    if not conn.execute(q, (pharmacist_id,)).fetchone():
        print("You are not registered as a dispenser.\n")
        return

    try:
        # Begin transaction
        conn.execute("BEGIN;")
        # Insert into Medication_dispensed
        conn.execute("""
            INSERT INTO Medication_dispensed (prescription_id, dispenser_id)
            VALUES (?, ?);
        """, (prescription_id, pharmacist_id))

        # Get all medications in the prescription
        meds = conn.execute("""
            SELECT medication_name FROM Contains WHERE prescription_id = ?;
        """, (prescription_id,)).fetchall()
        if not meds:
            raise Exception("No medications linked to this prescription.")

        # Decrement stock for each medication
        for med in meds:
            # Check current stock
            stock_row = conn.execute("SELECT quantity_in_stock FROM Medication WHERE name = ?;", (med['medication_name'],)).fetchone()
            if not stock_row or stock_row['quantity_in_stock'] <= 0:
                raise Exception(f"Not enough stock for medication: {med['medication_name']}")
            conn.execute("""
                UPDATE Medication SET quantity_in_stock = quantity_in_stock - 1 WHERE name = ?;
            """, (med['medication_name'],))

        conn.commit()
        print(f"Prescription {prescription_id} dispensed and medication stock updated.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error dispensing prescription: {e}\n")


def view_medication_inventory(conn):
    print("\n--- Medication Inventory ---")

    q = """
        SELECT name, quantity_in_stock, quantity_ordered, location
        FROM Medication
        ORDER BY name;
    """

    rows = conn.execute(q).fetchall()

    if not rows:
        print("No medications in inventory.\n")
        return

    print(f"{'Medication Name':<30} | {'In Stock':<10} | {'Ordered':<10} | {'Location':<25}")
    print("-" * 80)
    for r in rows:
        status = "⚠ LOW" if r['quantity_in_stock'] < 10 else "OK"
        print(f"{r['name']:<30} | {r['quantity_in_stock']:<10} | {r['quantity_ordered']:<10} | {r['location']:<25} {status}")
    print()


def update_medication_stock(conn):
    print("\n--- Update Medication Stock ---")

    medication_name = input("Enter medication name: ").strip()

    # Check if medication exists
    q = "SELECT * FROM Medication WHERE name = ?"
    med = conn.execute(q, (medication_name,)).fetchone()

    if not med:
        print("Medication not found.\n")
        return

    print(f"\nCurrent stock for '{medication_name}':")
    print(f"  In Stock: {med['quantity_in_stock']}")
    print(f"  Ordered: {med['quantity_ordered']}")

    try:
        new_stock = int(input("\nEnter new quantity in stock: ").strip())
        new_ordered = int(input("Enter new quantity ordered: ").strip())

        if new_stock <= 0 or new_ordered <= 0:
            print("Quantities must be positive.\n")
            return

        if new_ordered >= new_stock:
            print("Ordered quantity must be less than in-stock quantity.\n")
            return

        conn.execute("""
            UPDATE Medication
            SET quantity_in_stock = ?, quantity_ordered = ?
            WHERE name = ?;
        """, (new_stock, new_ordered, medication_name))
        conn.commit()
        print(f"Stock updated for '{medication_name}'.\n")

    except ValueError:
        print("Invalid input. Please enter valid numbers.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error updating stock: {e}\n")


#   PATIENT OPERATIONS
def list_patients(conn):
    print("\n--- Patient List ---")
    # NOTE: schema uses phone_number, not phone
    rows = conn.execute(
        "SELECT ssn, name, age, phone_number FROM Patient ORDER BY name;"
    ).fetchall()

    for r in rows:
        print(f"{r['ssn']}  |  {r['name']}  | Age {r['age']}  | {r['phone_number']}")
    print()



#   APPOINTMENTS
def list_appointments(conn):
    print("\n--- All Appointments ---")
    q = """
        SELECT A.appointment_id, A.scheduled_datetime, 
               P.name AS patient_name, D.name AS doctor_name
        FROM Appointment A
        JOIN Patient P ON A.patient_ssn = P.ssn
        JOIN Doctor D ON A.doctor_id = D.id
        ORDER BY A.scheduled_datetime;
    """
    rows = conn.execute(q).fetchall()
    for r in rows:
        print(f"{r['appointment_id']:3} | {r['scheduled_datetime']} | {r['patient_name']} | {r['doctor_name']}")
    print()


import sqlite3

def create_appointment(conn):
    print("\n--- Create Appointment ---")
    ssn = input("Patient SSN: ").strip()
    doctor_id = input("Doctor ID: ").strip()
    dt = input("DateTime (YYYY-MM-DD HH:MM:SS): ").strip()

    cur = conn.execute(
        "SELECT name FROM Patient WHERE ssn = ?;",
        (ssn,)
    )
    row = cur.fetchone()
    if row is None:
        print("Error: No patient found with that SSN.\n")
        return
    patient_name = row[0]

    try:
        conn.execute(
            """
            INSERT INTO Appointment (
                patient_ssn,
                patient_name,
                doctor_id,
                scheduled_datetime
            )
            VALUES (?, ?, ?, ?);
            """,
            (ssn, patient_name, doctor_id, dt),
        )
        conn.commit()
        print("Appointment created successfully.\n")
    except sqlite3.IntegrityError as e:
        print("Error:", e)

#list doctor

def list_doctors(conn):
    print("\n--- Doctor List ---")
    rows = conn.execute("""
        SELECT id, name, license_number, department_name
        FROM Doctor
        ORDER BY name;
    """).fetchall()

    for r in rows:
        print(f"ID: {r['id']} | {r['name']} | License: {r['license_number']} | Dept: {r['department_name']}")
    print()


#   PRESCRIPTIONS
def list_prescriptions_for_patient(conn):
    print("\n--- Patient Prescriptions ---")
    ssn = input("Enter patient SSN: ").strip()

    q = """
        SELECT Pr.prescription_id,
               Pr.dosage,
               D.name AS doctor_name
        FROM Prescription Pr
        JOIN Doctor D ON Pr.prescriber_id = D.id
        WHERE Pr.prescripted_patient_ssn = ?
        ORDER BY Pr.prescription_id DESC;
    """

    rows = conn.execute(q, (ssn,)).fetchall()

    if not rows:
        print("No prescriptions found.\n")
        return

    for r in rows:
        print(f"Prescription #{r['prescription_id']}  |  {r['dosage']}  | Dr. {r['doctor_name']}")
    print()



#   MEDICATION INVENTORY
def list_medications(conn):
    print("\n--- Medication Inventory ---")
    rows = conn.execute("""
        SELECT name, quantity_in_stock, quantity_ordered, location
        FROM Medication ORDER BY name;
    """).fetchall()

    for r in rows:
        print(f"{r['name']} | In Stock: {r['quantity_in_stock']} | Ordered: {r['quantity_ordered']} | Loc: {r['location']}")
    print()


#  for the login


#   DEPARTMENT MANAGEMENT
def list_departments(conn):
    print("\n--- Department List ---")
    
    q = """
        SELECT D.name, D.head_doctor_id, Doc.name AS head_doctor_name
        FROM Department D
        LEFT JOIN Doctor Doc ON D.head_doctor_id = Doc.id
        ORDER BY D.name;
    """
    
    rows = conn.execute(q).fetchall()
    
    if not rows:
        print("No departments found.\n")
        return
    
    print(f"{'Department':<30} | {'Head Doctor ID':<15} | {'Head Doctor Name':<25}")
    print("-" * 75)
    for r in rows:
        head = f"{r['head_doctor_name']} (ID: {r['head_doctor_id']})" if r['head_doctor_name'] else "Unassigned"
        print(f"{r['name']:<30} | {r['head_doctor_id'] or 'N/A':<15} | {head:<25}")
    print()


def view_department_details(conn):
    print("\n--- View Department Details ---")
    
    dept_name = input("Enter department name: ").strip()
    
    q = """
        SELECT D.name, D.head_doctor_id, Doc.name AS head_doctor_name,
               COUNT(Doc2.id) AS num_doctors
        FROM Department D
        LEFT JOIN Doctor Doc ON D.head_doctor_id = Doc.id
        LEFT JOIN Doctor Doc2 ON D.name = Doc2.department_name
        WHERE D.name = ?
        GROUP BY D.name;
    """
    
    row = conn.execute(q, (dept_name,)).fetchone()
    
    if not row:
        print("Department not found.\n")
        return
    
    print(f"\nDepartment: {row['name']}")
    print(f"Number of Doctors: {row['num_doctors']}")
    if row['head_doctor_name']:
        print(f"Head Doctor: {row['head_doctor_name']} (ID: {row['head_doctor_id']})")
    else:
        print(f"Head Doctor: Unassigned")
    
    # List all doctors in department
    q2 = "SELECT id, name, license_number FROM Doctor WHERE department_name = ? ORDER BY name;"
    doctors = conn.execute(q2, (dept_name,)).fetchall()
    
    if doctors:
        print("\nDoctors in this department:")
        for doc in doctors:
            print(f"  - {doc['name']} (ID: {doc['id']}, License: {doc['license_number']})")
    print()


def create_department(conn):
    print("\n--- Create New Department ---")
    
    dept_name = input("Enter department name: ").strip()
    
    if not dept_name:
        print("Department name cannot be empty.\n")
        return
    
    try:
        conn.execute("INSERT INTO Department (name) VALUES (?);", (dept_name,))
        conn.commit()
        print(f"Department '{dept_name}' created successfully.\n")
    except sqlite3.IntegrityError:
        print(f"Department '{dept_name}' already exists.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error creating department: {e}\n")


#   DOCTOR SPECIALIZATION
def view_specialist_doctors(conn):
    print("\n--- Specialist Doctors ---")
    
    q = """
        SELECT D.id, D.name, D.license_number, D.department_name, S.specialization
        FROM Doctor D
        JOIN Specialist S ON D.id = S.specialist_doctor_id
        ORDER BY D.name;
    """
    
    rows = conn.execute(q).fetchall()
    
    if not rows:
        print("No specialist doctors found.\n")
        return
    
    print(f"{'ID':<5} | {'Name':<20} | {'Specialization':<25} | {'Department':<20}")
    print("-" * 75)
    for r in rows:
        print(f"{r['id']:<5} | {r['name']:<20} | {r['specialization']:<25} | {r['department_name']:<20}")
    print()


def view_primary_care_doctors(conn):
    print("\n--- Primary Care Doctors ---")
    
    q = """
        SELECT D.id, D.name, D.license_number, D.department_name
        FROM Doctor D
        JOIN Primary_Care PC ON D.id = PC.primary_care_id
        ORDER BY D.name;
    """
    
    rows = conn.execute(q).fetchall()
    
    if not rows:
        print("No primary care doctors found.\n")
        return
    
    print(f"{'ID':<5} | {'Name':<20} | {'License':<15} | {'Department':<20}")
    print("-" * 65)
    for r in rows:
        print(f"{r['id']:<5} | {r['name']:<20} | {r['license_number']:<15} | {r['department_name']:<20}")
    print()


#   PHARMACY MANAGEMENT
def list_pharmacies(conn):
    print("\n--- Pharmacy List ---")
    
    q = """
        SELECT street, city, state, zip_code, telephone
        FROM Pharmacy
        ORDER BY city, street;
    """
    
    rows = conn.execute(q).fetchall()
    
    if not rows:
        print("No pharmacies found.\n")
        return
    
    print(f"{'Address':<50} | {'Phone':<15}")
    print("-" * 70)
    for r in rows:
        address = f"{r['street']}, {r['city']}, {r['state']} {r['zip_code']}"
        print(f"{address:<50} | {r['telephone']:<15}")
    print()


def view_pharmacy_details(conn):
    print("\n--- View Pharmacy Details ---")
    
    city = input("Enter pharmacy city: ").strip()
    street = input("Enter pharmacy street: ").strip()
    
    q = """
        SELECT street, city, state, zip_code, telephone
        FROM Pharmacy
        WHERE city = ? AND street = ?;
    """
    
    row = conn.execute(q, (city, street)).fetchone()
    
    if not row:
        print("Pharmacy not found.\n")
        return
    
    print(f"\nPharmacy Address: {row['street']}, {row['city']}, {row['state']} {row['zip_code']}")
    print(f"Telephone: {row['telephone']}")
    
    # List pharmacists at this location
    q2 = """
        SELECT id, name
        FROM Pharmacist
        WHERE pharmacy_city = ? AND pharmacy_street = ?
        ORDER BY name;
    """
    
    pharmacists = conn.execute(q2, (city, street)).fetchall()
    
    if pharmacists:
        print("\nPharmacists at this location:")
        for p in pharmacists:
            print(f"  - {p['name']} (ID: {p['id']})")
    print()


def create_pharmacy(conn):
    print("\n--- Create New Pharmacy ---")
    
    street = input("Enter street address: ").strip()
    city = input("Enter city: ").strip()
    state = input("Enter state: ").strip()
    zip_code = input("Enter zip code: ").strip()
    telephone = input("Enter telephone: ").strip()
    
    if not all([street, city, state, zip_code, telephone]):
        print("All fields are required.\n")
        return
    
    try:
        conn.execute("""
            INSERT INTO Pharmacy (street, city, state, zip_code, telephone)
            VALUES (?, ?, ?, ?, ?);
        """, (street, city, state, zip_code, telephone))
        conn.commit()
        print(f"Pharmacy in {city} created successfully.\n")
    except sqlite3.IntegrityError:
        print("This pharmacy already exists.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error creating pharmacy: {e}\n")


#   PHARMACIST ROLE MANAGEMENT
def view_pharmacist_details(conn):
    print("\n--- Pharmacist Details ---")
    
    pharmacist_id = input("Enter pharmacist ID: ").strip()
    
    q = """
        SELECT P.id, P.name, P.pharmacy_street, P.pharmacy_city, P.pharmacy_state, P.pharmacy_zip_code
        FROM Pharmacist P
        WHERE P.id = ?;
    """
    
    row = conn.execute(q, (pharmacist_id,)).fetchone()
    
    if not row:
        print("Pharmacist not found.\n")
        return
    
    print(f"\nPharmacist: {row['name']} (ID: {row['id']})")
    print(f"Pharmacy: {row['pharmacy_street']}, {row['pharmacy_city']}, {row['pharmacy_state']} {row['pharmacy_zip_code']}")
    
    # Check roles
    q2 = "SELECT * FROM Dispenser WHERE dispenser_id = ?;"
    is_dispenser = conn.execute(q2, (pharmacist_id,)).fetchone()
    
    q3 = "SELECT * FROM Inventory_manager WHERE inventory_manager_id = ?;"
    is_inventory_manager = conn.execute(q3, (pharmacist_id,)).fetchone()
    
    roles = []
    if is_dispenser:
        roles.append("Dispenser")
    if is_inventory_manager:
        roles.append("Inventory Manager")
    
    if roles:
        print(f"Roles: {', '.join(roles)}")
    else:
        print("Roles: None assigned")
    
    # If inventory manager, show managed medications
    if is_inventory_manager:
        q4 = """
            SELECT medication_name FROM Manages WHERE inventory_manager_id = ?
            ORDER BY medication_name;
        """
        meds = conn.execute(q4, (pharmacist_id,)).fetchall()
        
        if meds:
            print("\nManaged Medications:")
            for med in meds:
                print(f"  - {med['medication_name']}")
    print()


#   MEDICATION-PRESCRIPTION LINKING
def view_prescription_medications(conn):
    print("\n--- Prescription Medications ---")
    
    prescription_id = input("Enter prescription ID: ").strip()
    
    # First check if prescription exists
    q_check = "SELECT * FROM Prescription WHERE prescription_id = ?;"
    if not conn.execute(q_check, (prescription_id,)).fetchone():
        print("Prescription not found.\n")
        return
    
    q = """
        SELECT C.medication_name, M.quantity_in_stock, M.location
        FROM Contains C
        JOIN Medication M ON C.medication_name = M.name
        WHERE C.prescription_id = ?
        ORDER BY C.medication_name;
    """
    
    rows = conn.execute(q, (prescription_id,)).fetchall()
    
    if not rows:
        print(f"No medications linked to prescription {prescription_id}.\n")
        return
    
    print(f"\nMedications in Prescription {prescription_id}:")
    print(f"{'Medication':<30} | {'Stock':<10} | {'Location':<20}")
    print("-" * 65)
    for r in rows:
        print(f"{r['medication_name']:<30} | {r['quantity_in_stock']:<10} | {r['location']:<20}")
    print()


def add_medication_to_prescription(conn):
    print("\n--- Add Medication to Prescription ---")
    
    prescription_id = input("Enter prescription ID: ").strip()
    medication_name = input("Enter medication name: ").strip()
    
    # Check if prescription exists
    q_check = "SELECT * FROM Prescription WHERE prescription_id = ?;"
    if not conn.execute(q_check, (prescription_id,)).fetchone():
        print("Prescription not found.\n")
        return
    
    # Check if medication exists
    q_check2 = "SELECT * FROM Medication WHERE name = ?;"
    if not conn.execute(q_check2, (medication_name,)).fetchone():
        print("Medication not found.\n")
        return
    
    try:
        conn.execute("""
            INSERT INTO Contains (prescription_id, medication_name)
            VALUES (?, ?);
        """, (prescription_id, medication_name))
        conn.commit()
        print(f"Medication '{medication_name}' added to prescription {prescription_id}.\n")
    except sqlite3.IntegrityError:
        print("This medication is already linked to this prescription.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error adding medication: {e}\n")


def remove_medication_from_prescription(conn):
    print("\n--- Remove Medication from Prescription ---")
    
    prescription_id = input("Enter prescription ID: ").strip()
    medication_name = input("Enter medication name: ").strip()
    
    try:
        cursor = conn.execute("""
            DELETE FROM Contains
            WHERE prescription_id = ? AND medication_name = ?;
        """, (prescription_id, medication_name))
        
        if cursor.rowcount == 0:
            print("No matching medication found in prescription.\n")
        else:
            conn.commit()
            print(f"Medication '{medication_name}' removed from prescription {prescription_id}.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error removing medication: {e}\n")


#   PATIENT PRIMARY CARE ASSIGNMENT
def assign_primary_care_doctor(conn):
    print("\n--- Assign Primary Care Doctor ---")
    
    patient_ssn = input("Enter patient SSN: ").strip()
    patient_name = input("Enter patient name: ").strip()
    doctor_id = input("Enter doctor ID (primary care): ").strip()
    
    # Check patient exists
    q_check = "SELECT * FROM Patient WHERE ssn = ? AND name = ?;"
    if not conn.execute(q_check, (patient_ssn, patient_name)).fetchone():
        print("Patient not found.\n")
        return
    
    # Check doctor exists and is primary care
    q_check2 = """
        SELECT * FROM Primary_Care WHERE primary_care_id = ?;
    """
    if not conn.execute(q_check2, (doctor_id,)).fetchone():
        print("Doctor is not registered as a primary care physician.\n")
        return
    
    try:
        conn.execute("""
            UPDATE Patient
            SET primary_care_assigned_id = ?
            WHERE ssn = ? AND name = ?;
        """, (doctor_id, patient_ssn, patient_name))
        conn.commit()
        print(f"Primary care doctor assigned to patient successfully.\n")
    except Exception as e:
        conn.rollback()
        print(f"Error assigning primary care doctor: {e}\n")


def view_assigned_primary_care(conn):
    print("\n--- View Assigned Primary Care Doctor ---")
    
    patient_ssn = input("Enter patient SSN: ").strip()
    patient_name = input("Enter patient name: ").strip()
    
    q = """
        SELECT P.ssn, P.name, P.primary_care_assigned_id, D.name AS doctor_name, D.department_name
        FROM Patient P
        LEFT JOIN Primary_Care PC ON P.primary_care_assigned_id = PC.primary_care_id
        LEFT JOIN Doctor D ON PC.primary_care_id = D.id
        WHERE P.ssn = ? AND P.name = ?;
    """
    
    row = conn.execute(q, (patient_ssn, patient_name)).fetchone()
    
    if not row:
        print("Patient not found.\n")
        return
    
    print(f"\nPatient: {row['name']} (SSN: {row['ssn']})")
    if row['doctor_name']:
        print(f"Primary Care Doctor: {row['doctor_name']} (ID: {row['primary_care_assigned_id']}, Dept: {row['department_name']})")
    else:
        print("Primary Care Doctor: Not assigned")
    print()


def view_system_statistics(conn):
    print("\n--- System Statistics ---")
    
    # Count patients
    patients_count = conn.execute("SELECT COUNT(*) as count FROM Patient;").fetchone()['count']
    
    # Count doctors
    doctors_count = conn.execute("SELECT COUNT(*) as count FROM Doctor;").fetchone()['count']
    
    # Count appointments
    appointments_count = conn.execute("SELECT COUNT(*) as count FROM Appointment;").fetchone()['count']
    
    # Count prescriptions
    prescriptions_count = conn.execute("SELECT COUNT(*) as count FROM Prescription;").fetchone()['count']
    
    # Count departments
    departments_count = conn.execute("SELECT COUNT(*) as count FROM Department;").fetchone()['count']
    
    # Count pharmacies
    pharmacies_count = conn.execute("SELECT COUNT(*) as count FROM Pharmacy;").fetchone()['count']
    
    # Count pharmacists
    pharmacists_count = conn.execute("SELECT COUNT(*) as count FROM Pharmacist;").fetchone()['count']
    
    # Count medications
    medications_count = conn.execute("SELECT COUNT(*) as count FROM Medication;").fetchone()['count']
    
    # Count users
    users_count = conn.execute("SELECT COUNT(*) as count FROM User_Account;").fetchone()['count']
    
    print(f"\n{'Entity':<25} | {'Count':<10}")
    print("-" * 40)
    print(f"{'Patients':<25} | {patients_count:<10}")
    print(f"{'Doctors':<25} | {doctors_count:<10}")
    print(f"{'Appointments':<25} | {appointments_count:<10}")
    print(f"{'Prescriptions':<25} | {prescriptions_count:<10}")
    print(f"{'Departments':<25} | {departments_count:<10}")
    print(f"{'Pharmacies':<25} | {pharmacies_count:<10}")
    print(f"{'Pharmacists':<25} | {pharmacists_count:<10}")
    print(f"{'Medications':<25} | {medications_count:<10}")
    print(f"{'Users':<25} | {users_count:<10}")
    print()



def main():
    print(f"Connecting to database: {DB_PATH}")
    with get_connection() as conn:
        while True:
            print("""
===========================
     Welcome
===========================
1. Login
2. Register
0. Exit
""")
            choice = input("Select an option: ").strip()

            if choice == "1":
                user = login(conn)
                if user:
                    run_role_menu(conn, user)

            elif choice == "2":
                register_user(conn)

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print("Invalid choice.\n")


if __name__ == "__main__":
    main()

