import { X } from "lucide-react";
import { useEffect, useState } from "react";

export default function CrudModal({ fields, initial, title, error, saving, onClose, onSubmit }) {
  const [values, setValues] = useState(initial || {});
  useEffect(() => setValues(initial || {}), [initial]);
  function update(event) {
    setValues((current) => ({ ...current, [event.target.name]: event.target.value }));
  }
  function submit(event) {
    event.preventDefault();
    const payload = {};
    fields.forEach((field) => {
      const value = values[field.name];
      payload[field.name] = field.number && value !== "" ? Number(value) : value === "" ? null : value;
    });
    onSubmit(payload);
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-5"><h2 className="text-xl font-bold text-ink">{title}</h2><button aria-label="Close dialog" className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClose} type="button"><X size={20} /></button></div>
        <form className="grid gap-4 p-6 sm:grid-cols-2" onSubmit={submit}>
          {fields.map((field) => (
            <label className={field.full ? "block sm:col-span-2" : "block"} key={field.name}>
              <span className="mb-2 block text-sm font-semibold text-ink">{field.label}{field.required && <span className="ml-1 text-red-500">*</span>}</span>
              {field.options ? <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent" name={field.name} onChange={update} required={field.required} value={values[field.name] ?? ""}><option value="">Select</option>{field.options.map((option) => <option key={option.value ?? option} value={option.value ?? option}>{option.label ?? option}</option>)}</select> : field.textarea ? <textarea className="min-h-24 w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent" name={field.name} onChange={update} required={field.required} value={values[field.name] ?? ""} /> : <input className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent" name={field.name} onChange={update} required={field.required} type={field.type || "text"} value={values[field.name] ?? ""} />}
            </label>
          ))}
          {error && <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-700 sm:col-span-2">{error}</p>}
          <div className="flex justify-end gap-3 border-t border-border pt-5 sm:col-span-2"><button className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-ink" onClick={onClose} type="button">Cancel</button><button className="inline-flex min-w-28 items-center justify-center rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" disabled={saving} type="submit">{saving ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : "Save"}</button></div>
        </form>
      </div>
    </div>
  );
}
