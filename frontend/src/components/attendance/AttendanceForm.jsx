import { useEffect, useState } from "react";
import { X } from "lucide-react";

const emptyRecord = {
  employee_id: "",
  attendance_date: new Date().toISOString().slice(0, 10),
  status: "Present",
  in_time: "",
  out_time: "",
  remarks: "",
};

export default function AttendanceForm({
  attendance,
  employees,
  error,
  isSaving,
  onClose,
  onSubmit,
}) {
  const [form, setForm] = useState(emptyRecord);

  useEffect(() => {
    setForm(
      attendance
        ? { ...emptyRecord, ...attendance, employee_id: String(attendance.employee_id) }
        : emptyRecord,
    );
  }, [attendance]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSubmit({
      ...form,
      employee_id: Number(form.employee_id),
      in_time: form.in_time || null,
      out_time: form.out_time || null,
      remarks: form.remarks || null,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-5">
          <div>
            <h2 className="text-xl font-bold text-ink">
              {attendance ? "Edit attendance" : "Mark attendance"}
            </h2>
            <p className="mt-1 text-sm text-muted">Record the employee's attendance.</p>
          </div>
          <button aria-label="Close attendance form" className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClose} type="button">
            <X size={20} />
          </button>
        </div>
        <form className="space-y-5 p-6" onSubmit={submit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block sm:col-span-2">
              <span className="mb-2 block text-sm font-semibold text-ink">Employee<span className="ml-1 text-red-500">*</span></span>
              <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" name="employee_id" onChange={updateField} required value={form.employee_id}>
                <option value="">Select an employee</option>
                {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name} ({employee.employee_code})</option>)}
              </select>
            </label>
            <Field label="Attendance date" name="attendance_date" onChange={updateField} required type="date" value={form.attendance_date} />
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-ink">Status<span className="ml-1 text-red-500">*</span></span>
              <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" name="status" onChange={updateField} required value={form.status}>
                <option>Present</option>
                <option>Absent</option>
                <option>Leave</option>
                <option>Half Day</option>
              </select>
            </label>
            <Field label="Check-in time" name="in_time" onChange={updateField} type="time" value={form.in_time || ""} />
            <Field label="Check-out time" name="out_time" onChange={updateField} type="time" value={form.out_time || ""} />
            <label className="block sm:col-span-2">
              <span className="mb-2 block text-sm font-semibold text-ink">Notes</span>
              <textarea className="min-h-24 w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" name="remarks" onChange={updateField} placeholder="Optional remarks" value={form.remarks || ""} />
            </label>
          </div>
          {error && <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-3 border-t border-border pt-5">
            <button className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-ink hover:bg-canvas" onClick={onClose} type="button">Cancel</button>
            <button className="inline-flex min-w-32 items-center justify-center rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#126C88] disabled:opacity-60" disabled={isSaving} type="submit">
              {isSaving ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : attendance ? "Save changes" : "Mark attendance"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, name, onChange, required, type = "text", value }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-ink">{label}{required && <span className="ml-1 text-red-500">*</span>}</span>
      <input className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" name={name} onChange={onChange} required={required} type={type} value={value ?? ""} />
    </label>
  );
}
