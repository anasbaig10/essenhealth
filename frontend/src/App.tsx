import React, { useEffect, useState } from "react";
import { fetchPatients, PatientResponse } from "./api/patients";
import RoleToggle from "./components/RoleToggle";
import FilterBar from "./components/FilterBar";
import PatientTable from "./components/PatientTable";

export default function App() {
  const [role, setRole] = useState<"scheduler" | "clinical">("scheduler");
  const [specialty, setSpecialty] = useState("");
  const [taskType, setTaskType] = useState("");
  const [patients, setPatients] = useState<PatientResponse[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const data = await fetchPatients({
          role,
          specialty: specialty || undefined,
          task_type: taskType || undefined,
        });
        if (!cancelled) setPatients(data.patients);
      } catch (err) {
        if (!cancelled) setPatients([]);
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [role, specialty, taskType]);

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        minHeight: "100vh",
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "32px",
        }}
      >
        {/* Title block */}
        <div>
          <h1
            style={{
              fontSize: "20px",
              fontWeight: 600,
              color: "#1a1a1a",
              margin: 0,
            }}
          >
            Clinical Worklist
          </h1>
          <p
            style={{
              fontSize: "14px",
              color: "#6b7280",
              margin: "4px 0 0 0",
            }}
          >
            {patients.length} patient{patients.length !== 1 ? "s" : ""} with active tasks
          </p>
        </div>

        {/* Controls row */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "24px",
          }}
        >
          <RoleToggle role={role} onRoleChange={setRole} />
          <FilterBar
            specialty={specialty}
            taskType={taskType}
            onSpecialtyChange={setSpecialty}
            onTaskTypeChange={setTaskType}
          />
        </div>

        {/* Table */}
        <div style={{ marginTop: "16px" }}>
          <PatientTable patients={patients} loading={loading} />
        </div>
      </div>
    </div>
  );
}
