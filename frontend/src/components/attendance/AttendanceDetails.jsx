import { X } from "lucide-react";

export default function AttendanceDetails({ attendance, employeeName, onClose }) {
  if (!attendance) return null;
  const fields = [
    ["Attendance ID", attendance.id],
    ["Employee ID", attendance.employee_code || `Employee #${attendance.employee_id}`],
    ["Employee name", attendance.employee_name || employeeName],
    ["Attendance date", attendance.attendance_date],
    ["Status", attendance.status],
    ["Check-in time", attendance.in_time],
    ["Check-out time", attendance.out_time],
    ["Notes", attendance.remarks],
  ];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-5">
          <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Attendance details</p><h2 className="mt-1 text-xl font-bold text-ink">{attendance.employee_name || employeeName || `Record #${attendance.id}`}</h2></div>
          <button aria-label="Close attendance details" className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClose} type="button"><X size={20} /></button>
        </div>
        <dl className="grid gap-4 p-6 sm:grid-cols-2">
          {fields.map(([label, value]) => <div key={label}><dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt><dd className="mt-1 text-sm font-semibold text-ink">{value || "—"}</dd></div>)}
        </dl>
      </div>
    </div>
  );
}
