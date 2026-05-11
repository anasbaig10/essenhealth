const BASE_URL = "";

export interface TaskResponse {
  specialty: string;
  task_type: "scheduling" | "referral";
  need_type: string;
  cadence_days: number;
  last_visit: string | null;
  days_overdue: number | null;
}

export interface EnrollmentResponse {
  program: string;
  tier: string;
  tasks: TaskResponse[];
}

export interface PatientResponse {
  patient_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  programs: EnrollmentResponse[];
}

export interface PatientListResponse {
  patients: PatientResponse[];
  total: number;
}

export async function fetchPatients(params: {
  role?: "scheduler" | "clinical";
  specialty?: string;
  task_type?: string;
}): Promise<PatientListResponse> {
  const query = new URLSearchParams();

  if (params.role) query.set("role", params.role);
  if (params.specialty) query.set("specialty", params.specialty);
  if (params.task_type) query.set("task_type", params.task_type);

  const qs = query.toString();
  const url = `${BASE_URL}/patients${qs ? `?${qs}` : ""}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Failed to fetch patients: ${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<PatientListResponse>;
}
