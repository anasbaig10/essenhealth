from datetime import date
from config import REFERENCE_DATE, HBAIC_CUTOFF


def generate_task(patient_id: str, need, conn) -> dict | None:
    # Step 1 — future appointment exists → no task
    future_rows = conn.execute(
        """
        SELECT 1 FROM encounters
        WHERE patient_id = ? AND specialty = ? AND is_future = 1
        """,
        (patient_id, need.specialty),
    ).fetchall()
    if future_rows:
        return None

    # Step 2 — get past encounters for this specialty
    past_rows = conn.execute(
        """
        SELECT encounter_date FROM encounters
        WHERE patient_id = ? AND specialty = ? AND is_future = 0
        ORDER BY encounter_date DESC
        """,
        (patient_id, need.specialty),
    ).fetchall()

    # Step 3 — never seen this specialty before
    if not past_rows:
        if need.specialty == "PCP":
            return None
        return {
            "specialty": need.specialty,
            "task_type": "referral",
            "need_type": need.need_type,
            "cadence_days": need.cadence_days,
            "last_visit": None,
            "days_overdue": None,
        }

    # Step 4 — past encounter exists
    last_visit_date = date.fromisoformat(past_rows[0]["encounter_date"])
    days_since = (REFERENCE_DATE - last_visit_date).days
    if days_since > need.cadence_days:
        return {
            "specialty": need.specialty,
            "task_type": "scheduling",
            "need_type": need.need_type,
            "cadence_days": need.cadence_days,
            "last_visit": str(last_visit_date),
            "days_overdue": days_since - need.cadence_days,
        }
    return None


def handle_lab_order(patient_id, need, conn):
    # Check if patient had this lab recently
    recent = conn.execute("""
        SELECT result_date FROM labs
        WHERE patient_id = ?
        AND test_name = ?
        AND result_date >= ?
        ORDER BY result_date DESC
        LIMIT 1
    """, (patient_id, need.specialty, str(HBAIC_CUTOFF))).fetchone()

    if recent:
        return None  # lab done recently, no task needed

    return {
        "specialty": need.specialty,
        "task_type": "lab_order",
        "need_type": need.need_type,
        "cadence_days": need.cadence_days,
        "last_visit": None,
        "days_overdue": None,
    }


TASK_HANDLERS = {
    "specialist_visit": generate_task,
    "lab_order": handle_lab_order,
}
