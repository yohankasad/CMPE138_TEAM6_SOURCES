
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "SQL"
DB_PATH = SQL_DIR / "schema.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


#   PATIENT OPERATIONS

def list_patients(conn):
    print("\n--- Patient List ---")
    rows = conn.execute("SELECT ssn, name, age, phone FROM Patient ORDER BY name;").fetchall()
    for r in rows:
        print(f"{r['ssn']}  |  {r['name']}  | Age {r['age']}  | {r['phone']}")
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
        print(f"{r['appointment_id']:3} | {r['scheduled_datetime']} | {r['patient_name']} | Dr. {r['doctor_name']}")
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


#   PRESCRIPTIONS

def list_prescriptions_for_patient(conn):
    print("\n--- Patient Prescriptions ---")
    ssn = input("Enter patient SSN: ").strip()

    q = """
        SELECT Pr.prescription_id, Pr.date, D.name AS doctor_name
        FROM Prescription Pr
        JOIN Doctor D ON Pr.doctor_id = D.id
        WHERE Pr.patient_ssn = ?
        ORDER BY Pr.date DESC;
    """

    rows = conn.execute(q, (ssn,)).fetchall()

    if not rows:
        print("No prescriptions found.\n")
        return

    for r in rows:
        print(f"Prescription #{r['prescription_id']}  |  {r['date']}  | Dr. {r['doctor_name']}")
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


#   MENU LOOP

def menu(conn):
    while True:
        print("""
============================
 Healthcare Management App
============================
1. List Patients
2. List Appointments
3. Create Appointment
4. View Patient Prescriptions
5. View Medication Inventory
0. Exit
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
        elif choice == "0":
            print("Exiting…")
            break
        else:
            print("Invalid choice. Try again.\n")


#   MAIN

def main():
    print(f"Connecting to database: {DB_PATH}")
    with get_connection() as conn:
        menu(conn)


if __name__ == "__main__":
    main()