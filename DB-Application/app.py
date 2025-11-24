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
6. List Doctor
9. Register New User
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
        elif choice == "9":
            register_user(conn)
        elif choice == "6":
            list_doctors(conn)
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
    print("\n--- Patient Menu (coming soon) ---\n")


def pharmacist_menu(conn, user):
    print("\n--- Pharmacist Menu (coming soon) ---\n")


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


def create_appointment(conn):
    print("\n--- Create Appointment ---")
    ssn = input("Patient SSN: ").strip()
    doctor_id = input("Doctor ID: ").strip()
    dt = input("DateTime (YYYY-MM-DD HH:MM:SS): ").strip()

    try:
        conn.execute("""
            INSERT INTO Appointment (patient_ssn, doctor_id, scheduled_datetime)
            VALUES (?, ?, ?);
        """, (ssn, doctor_id, dt))
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
