import React from "react";

interface Props {
  role: "scheduler" | "clinical";
  onRoleChange: (role: "scheduler" | "clinical") => void;
}

const ROLES: { value: "scheduler" | "clinical"; label: string }[] = [
  { value: "scheduler", label: "Scheduler" },
  { value: "clinical", label: "Clinical Team" },
];

export default function RoleToggle({ role, onRoleChange }: Props) {
  return (
    <div style={{ display: "flex" }}>
      {ROLES.map(({ value, label }) => {
        const isActive = role === value;
        return (
          <button
            key={value}
            onClick={() => onRoleChange(value)}
            style={{
              padding: "8px 20px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: 500,
              border: "1px solid #d1d5db",
              borderLeft: value === "clinical" ? "none" : "1px solid #d1d5db",
              backgroundColor: isActive ? "#1a1a1a" : "#ffffff",
              color: isActive ? "#ffffff" : "#1a1a1a",
              borderRadius:
                value === "scheduler" ? "4px 0 0 4px" : "0 4px 4px 0",
              boxShadow: "none",
              outline: "none",
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
