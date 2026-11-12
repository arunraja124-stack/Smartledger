import { useEffect, useState } from "react";
import { X } from "lucide-react";

const emptyEmployee = {
  employee_code: "",
  full_name: "",
  department: "",
  designation: "",
  branch: "",
  contact_number: "",
  joining_date: "",
  employment_status: "Active",
};

export default function EmployeeForm({ employee, isSaving, error, onClose, onSubmit }) {
  const [form, setForm] = useState(emptyEmployee);

  useEffect(() => {
    setForm(employee ? { ...emptyEmployee, ...employee } : emptyEmployee);
  }, [employee]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function submit(event) {
    event.preventDefault();
    const required = ["employee_code", "full_name"];
    if (required.some((field) => !form[field].trim())) return;
    onSubmit({
      ...form,
      department: form.department || null,
      designation: form.designation || null,
      branch: form.branch || null,
      contact_number: form.contact_number || null,
      joining_date: form.joining_date || null,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-5">
          <div>
            <h2 className="text-xl font-bold text-ink">{employee ? "Edit employee" : "Add employee"}</h2>
            <p className="mt-1 text-sm text-muted">Enter the employee register details.</p>
          </div>
          <button aria-label="Close form" className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClose} type="button"><X size={20} /></button>
        </div>
        <form className="space-y-5 p-6" onSubmit={submit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Employee code" name="employee_code" required value={form.employee_code} onChange={updateField} />
            <Field label="Full name" name="full_name" required value={form.full_name} onChange={updateField} />
            <Field label="Department" name="department" value={form.department} onChange={updateField} />
            <Field label="Designation" name="designation" value={form.designation} onChange={updateField} />
            <Field label="Branch" name="branch" value={form.branch} onChange={updateField} />
            <Field label="Contact number" name="contact_number" value={form.contact_number} onChange={updateField} />
            <Field label="Joining date" name="joining_date" type="date" value={form.joining_date || ""} onChange={updateField} />
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-ink">Employment status</span>
              <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" name="employment_status" onChange={updateField} value={form.employment_status}>
                <option>Active</option>
                <option>Inactive</option>
                <option>On Leave</option>
              </select>
            </label>
          </div>
          {error && <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-3 border-t border-border pt-5">
            <button className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-ink hover:bg-canvas" onClick={onClose} type="button">Cancel</button>
            <button className="inline-flex min-w-28 items-center justify-center rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#126C88] disabled:opacity-60" disabled={isSaving} type="submit">
              {isSaving ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : employee ? "Save changes" : "Add employee"}
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
