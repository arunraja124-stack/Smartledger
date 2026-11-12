import { X } from "lucide-react";

export default function EmployeeDetails({ employee, onClose }) {
  if (!employee) return null;
  const fields = [
    ["Employee ID", employee.id],
    ["Employee code", employee.employee_code],
    ["Full name", employee.full_name],
    ["Department", employee.department],
    ["Designation", employee.designation],
    ["Branch", employee.branch],
    ["Contact number", employee.contact_number],
    ["Joining date", employee.joining_date],
    ["Employment status", employee.employment_status],
  ];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-5">
          <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Employee details</p><h2 className="mt-1 text-xl font-bold text-ink">{employee.full_name}</h2></div>
          <button aria-label="Close details" className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClose} type="button"><X size={20} /></button>
        </div>
        <dl className="grid gap-4 p-6 sm:grid-cols-2">
          {fields.map(([label, value]) => <div key={label}><dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt><dd className="mt-1 text-sm font-semibold text-ink">{value || "—"}</dd></div>)}
        </dl>
      </div>
    </div>
  );
}
