import React from "react";

interface Props {
  specialty: string;
  taskType: string;
  onSpecialtyChange: (specialty: string) => void;
  onTaskTypeChange: (taskType: string) => void;
}

const SPECIALTIES = [
  "All",
  "PCP",
  "Endocrinology",
  "Cardiology",
  "Podiatry",
  "Ophthalmology",
  "Nephrology",
];

const TASK_TYPES = ["All", "Scheduling", "Referral"];

const selectStyle: React.CSSProperties = {
  border: "1px solid #d1d5db",
  padding: "6px 12px",
  fontSize: "14px",
  backgroundColor: "#ffffff",
  color: "#1a1a1a",
  cursor: "pointer",
};

const labelStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0",
  fontSize: "13px",
  color: "#6b7280",
};

export default function FilterBar({
  specialty,
  taskType,
  onSpecialtyChange,
  onTaskTypeChange,
}: Props) {
  return (
    <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
      <label style={labelStyle}>
        <span style={{ marginRight: "6px" }}>Specialty:</span>
        <select
          value={specialty || "All"}
          onChange={(e) =>
            onSpecialtyChange(e.target.value === "All" ? "" : e.target.value)
          }
          style={selectStyle}
        >
          {SPECIALTIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>

      <label style={labelStyle}>
        <span style={{ marginRight: "6px" }}>Task Type:</span>
        <select
          value={
            taskType
              ? taskType.charAt(0).toUpperCase() + taskType.slice(1)
              : "All"
          }
          onChange={(e) =>
            onTaskTypeChange(
              e.target.value === "All" ? "" : e.target.value.toLowerCase()
            )
          }
          style={selectStyle}
        >
          {TASK_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
