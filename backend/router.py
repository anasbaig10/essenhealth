import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_connection
from models import (
    EnrollmentResponse,
    PatientListResponse,
    PatientResponse,
    TaskResponse,
)

router = APIRouter()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _build_patient_response(patient_row, rows) -> PatientResponse:
    """Convert flat task rows into nested PatientResponse."""
    programs_dict: dict = {}
    for row in rows:
        prog_key = row["program"]
        if prog_key not in programs_dict:
            programs_dict[prog_key] = {
                "program": prog_key,
                "tier": row["tier"],
                "tasks": [],
            }
        programs_dict[prog_key]["tasks"].append(
            TaskResponse(
                specialty=row["specialty"],
                task_type=row["task_type"],
                need_type=row["need_type"],
                cadence_days=row["cadence_days"],
                last_visit=row["last_visit"],
                days_overdue=row["days_overdue"],
            )
        )

    programs = [
        EnrollmentResponse(
            program=p["program"],
            tier=p["tier"],
            tasks=p["tasks"],
        )
        for p in programs_dict.values()
    ]

    return PatientResponse(
        patient_id=patient_row["patient_id"],
        first_name=patient_row["first_name"],
        last_name=patient_row["last_name"],
        date_of_birth=patient_row["date_of_birth"],
        programs=programs,
    )


@router.get("/patients", response_model=PatientListResponse)
def list_patients(
    specialty: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    conn: sqlite3.Connection = Depends(get_db),
) -> PatientListResponse:
    sql = """
        SELECT
            p.patient_id, p.first_name, p.last_name, p.date_of_birth,
            e.program, e.tier,
            t.specialty, t.task_type, t.need_type,
            t.cadence_days, t.last_visit, t.days_overdue
        FROM tasks t
        JOIN patients p ON t.patient_id = p.patient_id
        JOIN enrollments e
            ON t.patient_id = e.patient_id AND t.program = e.program
        WHERE 1=1
    """
    params: list = []

    # Role filter
    if role == "scheduler":
        sql += " AND t.task_type = 'scheduling'"
    # role == "clinical" or None → no additional filter

    # Specialty filter
    if specialty:
        sql += " AND t.specialty = ?"
        params.append(specialty)

    # task_type filter
    if task_type:
        sql += " AND t.task_type = ?"
        params.append(task_type)

    sql += " ORDER BY p.patient_id, e.program, t.specialty"

    rows = conn.execute(sql, params).fetchall()

    # Group flat rows → patient → program → tasks
    patients_dict: dict = {}
    patient_meta: dict = {}
    for row in rows:
        pid = row["patient_id"]
        if pid not in patients_dict:
            patients_dict[pid] = {}
            patient_meta[pid] = row

        prog_key = row["program"]
        if prog_key not in patients_dict[pid]:
            patients_dict[pid][prog_key] = {
                "program": prog_key,
                "tier": row["tier"],
                "tasks": [],
            }
        patients_dict[pid][prog_key]["tasks"].append(
            TaskResponse(
                specialty=row["specialty"],
                task_type=row["task_type"],
                need_type=row["need_type"],
                cadence_days=row["cadence_days"],
                last_visit=row["last_visit"],
                days_overdue=row["days_overdue"],
            )
        )

    patient_list = []
    for pid, programs_map in patients_dict.items():
        meta = patient_meta[pid]
        programs = [
            EnrollmentResponse(
                program=p["program"],
                tier=p["tier"],
                tasks=p["tasks"],
            )
            for p in programs_map.values()
        ]
        patient_list.append(
            PatientResponse(
                patient_id=meta["patient_id"],
                first_name=meta["first_name"],
                last_name=meta["last_name"],
                date_of_birth=meta["date_of_birth"],
                programs=programs,
            )
        )

    return PatientListResponse(patients=patient_list, total=len(patient_list))


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> PatientResponse:
    patient_row = conn.execute(
        "SELECT patient_id, first_name, last_name, date_of_birth FROM patients WHERE patient_id = ?",
        (patient_id,),
    ).fetchone()

    if patient_row is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    rows = conn.execute(
        """
        SELECT
            e.program, e.tier,
            t.specialty, t.task_type, t.need_type,
            t.cadence_days, t.last_visit, t.days_overdue
        FROM tasks t
        JOIN enrollments e
            ON t.patient_id = e.patient_id AND t.program = e.program
        WHERE t.patient_id = ?
        ORDER BY e.program, t.specialty
        """,
        (patient_id,),
    ).fetchall()

    return _build_patient_response(patient_row, rows)
