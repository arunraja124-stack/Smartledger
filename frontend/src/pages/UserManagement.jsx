import { KeyRound, Pencil, Plus, RefreshCw, UserCheck, UserRoundX } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { createUser, listUsers, resetUserPassword, updateUser } from "../services/adminService";

const emptyForm = { full_name: "", email: "", password: "", role: "Staff", is_active: true };
const generatedPassword = () => `${crypto.randomUUID()}${crypto.randomUUID()}`;

export default function UserManagement() {
  const [result, setResult] = useState({ items: [], total: 0 });
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { setResult(await listUsers()); setError(""); }
    catch (loadError) { setError(loadError.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  function openCreate() {
    setEditing(null); setForm({ ...emptyForm, password: generatedPassword() });
    setError(""); setShowForm(true);
  }
  function openEdit(user) {
    setEditing(user); setForm({ full_name: user.full_name, email: user.email, role: user.role === "Admin" ? "Admin" : "Staff", is_active: user.is_active });
    setError(""); setShowForm(true);
  }
  async function save(event) {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    try {
      if (editing) await updateUser(editing.id, { full_name: form.full_name, email: form.email, role: form.role, is_active: form.is_active });
      else await createUser(form);
      setShowForm(false); setNotice(editing ? "User details updated." : "User account created. Share the temporary password securely."); await load();
    } catch (saveError) { setError(saveError.message); }
    finally { setSaving(false); }
  }
  async function toggle(user) {
    setError(""); setNotice("");
    try { await updateUser(user.id, { is_active: !user.is_active }); setNotice(`${user.full_name} is now ${user.is_active ? "inactive" : "active"}.`); await load(); }
    catch (updateError) { setError(updateError.message); }
  }
  async function reset(user) {
    setError(""); setNotice("");
    try {
      const result = await resetUserPassword(user.id);
      setNotice(`Temporary password for ${user.full_name}: ${result.temporary_password}`);
    } catch (resetError) { setError(resetError.message); }
  }

  return <div className="space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">Administration</p><h2 className="mt-1 text-2xl font-bold text-ink">User Management</h2><p className="mt-1 text-sm text-muted">Create accounts and manage workspace access.</p></div><button className="inline-flex items-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white" onClick={openCreate} type="button"><Plus size={17} /> Create user</button></div>
    {notice && <p className="break-all rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
    {error && <p className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
    <section className="overflow-x-auto rounded-2xl border border-border bg-white shadow-sm"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-canvas text-xs uppercase text-muted"><tr><th className="px-5 py-4">User</th><th className="px-5 py-4">Role</th><th className="px-5 py-4">Status</th><th className="px-5 py-4 text-right">Actions</th></tr></thead><tbody className="divide-y divide-border">{loading ? <tr><td className="px-5 py-8 text-center text-muted" colSpan="4">Loading users…</td></tr> : result.items.length ? result.items.map((user) => <tr key={user.id}><td className="px-5 py-4"><p className="font-semibold text-ink">{user.full_name}</p><p className="text-xs text-muted">{user.email}</p></td><td className="px-5 py-4">{user.role === "Admin" ? "Admin" : "Staff"}</td><td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${user.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{user.is_active ? "Active" : "Inactive"}</span></td><td className="px-5 py-4"><div className="flex justify-end gap-1"><Action label={`Edit ${user.full_name}`} onClick={() => openEdit(user)}><Pencil size={17} /></Action><Action label={`Reset password for ${user.full_name}`} onClick={() => reset(user)}><KeyRound size={17} /></Action><Action label={`${user.is_active ? "Deactivate" : "Activate"} ${user.full_name}`} onClick={() => toggle(user)}>{user.is_active ? <UserRoundX size={17} /> : <UserCheck size={17} />}</Action></div></td></tr>) : <tr><td className="px-5 py-8 text-center text-muted" colSpan="4">No users found.</td></tr>}</tbody></table><div className="border-t border-border px-5 py-3 text-xs text-muted">{result.total} registered users</div></section>
    {showForm && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"><form className="w-full max-w-xl space-y-4 rounded-2xl bg-white p-6 shadow-2xl" onSubmit={save}><div><h3 className="text-xl font-bold text-ink">{editing ? "Edit user" : "Create user account"}</h3><p className="mt-1 text-sm text-muted">Passwords are hashed before they are stored.</p></div><Field label="Full name"><input autoComplete="name" className={inputClass} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required value={form.full_name} /></Field><Field label="Email address"><input autoComplete="email" className={inputClass} onChange={(e) => setForm({ ...form, email: e.target.value })} required type="email" value={form.email} /></Field><Field label="Role"><select className={inputClass} onChange={(e) => setForm({ ...form, role: e.target.value })} value={form.role}><option value="Staff">Staff</option><option value="Admin">Admin</option></select></Field>{!editing && <Field label="Temporary password"><div className="flex gap-2"><input autoComplete="new-password" className={inputClass} minLength={8} onChange={(e) => setForm({ ...form, password: e.target.value })} required value={form.password} /><button className="shrink-0 rounded-xl border border-border px-3 text-sm" onClick={() => setForm({ ...form, password: generatedPassword() })} title="Generate secure password" type="button"><RefreshCw size={16} /></button></div></Field>}{editing && <label className="flex items-center gap-2 text-sm text-ink"><input checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} type="checkbox" /> Account active</label>}{error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}<div className="flex justify-end gap-3 pt-2"><button className="rounded-xl border border-border px-4 py-2.5 text-sm" onClick={() => setShowForm(false)} type="button">Cancel</button><button className="rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" disabled={saving} type="submit">{saving ? "Saving…" : editing ? "Save changes" : "Create account"}</button></div></form></div>}
  </div>;
}

function Field({ label, children }) { return <label className="block"><span className="mb-2 block text-sm font-semibold text-ink">{label}</span>{children}</label>; }
function Action({ label, onClick, children }) { return <button aria-label={label} className="rounded-lg p-2 text-muted hover:bg-canvas" onClick={onClick} title={label} type="button">{children}</button>; }
const inputClass = "w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm text-ink outline-none focus:border-accent";
