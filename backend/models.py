from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class TaskResponse(BaseModel):
    specialty: str
    task_type: str
    need_type: str
    cadence_days: int
    last_visit: Optional[date]
    days_overdue: Optional[int]


class EnrollmentResponse(BaseModel):
    program: str
    tier: str
    tasks: List[TaskResponse]


class PatientResponse(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    programs: List[EnrollmentResponse]


class PatientListResponse(BaseModel):
    patients: List[PatientResponse]
    total: int
