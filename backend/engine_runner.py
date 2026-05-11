from datetime import datetime
from rules_engine import PROGRAM_REGISTRY
from task_generator import TASK_HANDLERS


def run_engine(conn) -> None:
    cursor = conn.cursor()

    # Step 1 — clear previous results
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM enrollments")

    # Step 4 — fetch all patients
    patients = conn.execute("SELECT patient_id FROM patients").fetchall()

    enrollment_count = 0
    task_count = 0
    scheduling_count = 0
    referral_count = 0

    now = datetime.now().isoformat()

    # Step 5 — evaluate each patient against every program
    for patient_row in patients:
        patient_id = patient_row["patient_id"]

        for program in PROGRAM_REGISTRY:
            if not program.check_eligibility(patient_id, conn):
                continue

            tier = program.get_tier(patient_id, conn)
            cursor.execute(
                """
                INSERT INTO enrollments (patient_id, program, tier, evaluated_at)
                VALUES (?, ?, ?, ?)
                """,
                (patient_id, program.program_name, tier, now),
            )
            enrollment_count += 1

            needs = program.get_needs(tier)
            for need in needs:
                handler = TASK_HANDLERS[need.need_type]
                result = handler(patient_id, need, conn)
                if result is not None:
                    cursor.execute(
                        """
                        INSERT INTO tasks (
                            patient_id, program, specialty, task_type,
                            need_type, cadence_days, last_visit,
                            days_overdue, evaluated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patient_id,
                            program.program_name,
                            result["specialty"],
                            result["task_type"],
                            result["need_type"],
                            result["cadence_days"],
                            result["last_visit"],
                            result["days_overdue"],
                            now,
                        ),
                    )
                    task_count += 1
                    if result["task_type"] == "scheduling":
                        scheduling_count += 1
                    else:
                        referral_count += 1

    # Step 6 — commit
    conn.commit()

    # Step 7 — summary
    print(
        f"Engine complete: {enrollment_count} enrollments, {task_count} tasks "
        f"({scheduling_count} scheduling, {referral_count} referral)"
    )
