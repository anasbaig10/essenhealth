import React from "react";
import { PatientResponse } from "../api/patients";

interface Props {
  patients: PatientResponse[];
  loading: boolean;
}

interface FlatRow {
  patientName: string;
  showName: boolean;
  program: string;
  tier: string;
  specialty: string;
  task_type: string;
  days_overdue: number | null;
}

function flattenPatients(patients: PatientResponse[]): FlatRow[] {
  const rows: FlatRow[] = [];

  for (const patient of patients) {
    const fullName = `${patient.first_name} ${patient.last_name}`;
    let firstRow = true;

    for (const enrollment of patient.programs) {
      for (const task of enrollment.tasks) {
        rows.push({
          patientName: fullName,
          showName: firstRow,
          program: enrollment.program,
          tier: enrollment.tier,
          specialty: task.specialty,
          task_type: task.task_type,
          days_overdue: task.days_overdue,
        });
        firstRow = false;
      }
    }
  }

  return rows;
}

const thStyle: React.CSSProperties = {
  padding: "10px 16px",
  textAlign: "left",
  fontSize: "12px",
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  color: "#6b7280",
  backgroundColor: "#f9fafb",
  borderBottom: "1px solid #e5e7eb",
};

const tdStyle: React.CSSProperties = {
  padding: "12px 16px",
  fontSize: "14px",
  color: "#1a1a1a",
  borderBottom: "1px solid #f3f4f6",
};

const centeredMsg: React.CSSProperties = {
  padding: "48px 0",
  textAlign: "center",
  fontSize: "14px",
  color: "#6b7280",
};

export default function PatientTable({ patients, loading }: Props) {
  if (loading) {
    return <div style={centeredMsg}>Loading...</div>;
  }

  if (patients.length === 0) {
    return <div style={centeredMsg}>No patients found</div>;
  }

  const rows = flattenPatients(patients);

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", borderTop: "1px solid #e5e7eb" }}>
        <thead>
          <tr>
            <th style={thStyle}>Patient Name</th>
            <th style={thStyle}>Program</th>
            <th style={thStyle}>Tier</th>
            <th style={thStyle}>Specialty</th>
            <th style={thStyle}>Task Type</th>
            <th style={thStyle}>Days Overdue</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ backgroundColor: "#ffffff" }}>
              <td style={{ ...tdStyle, fontWeight: row.showName ? 600 : 400 }}>
                {row.showName ? row.patientName : ""}
              </td>
              <td style={tdStyle}>{row.program}</td>
              <td style={tdStyle}>{row.tier}</td>
              <td style={tdStyle}>{row.specialty}</td>
              <td style={tdStyle}>
                {row.task_type.charAt(0).toUpperCase() + row.task_type.slice(1)}
              </td>
              <td style={tdStyle}>
                {row.days_overdue === null ? "First Visit" : `${row.days_overdue}d`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
