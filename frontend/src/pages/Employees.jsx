import { Eye, Pencil, Plus, Search, Trash2, Users, ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import EmployeeDetails from "../components/employees/EmployeeDetails";
import EmployeeForm from "../components/employees/EmployeeForm";
import { createEmployee, deleteEmployee, getEmployee, listEmployees, updateEmployee } from "../services/employeeService";

const pageSize = 10;

export default function Employees() {
  const [result, setResult] = useState({ items: [], total: 0, page: 1, page_size: pageSize });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState(null);
  const [selected, setSelected] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const loadEmployees = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      setResult(await listEmployees(page, pageSize));
    } catch (loadError) {
      setError(loadError.message || "Unable to load employees.");
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => { loadEmployees(); }, [loadEmployees]);
  useEffect(() => { setPage(1); }, [search]);

  const visibleEmployees = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return result.items;
    return result.items.filter((employee) =>
      [employee.employee_code, employee.full_name, employee.department, employee.designation, employee.branch, employee.contact_number, employee.employment_status]
        .some((value) => String(value || "").toLowerCase().includes(term)),
    );
  }, [result.items, search]);

  async function saveEmployee(payload) {
    setIsSaving(true);
    setError("");
    try {
      if (modal === "edit") await updateEmployee(selected.id, payload);
      else await createEmployee(payload);
      setModal(null);
      setSelected(null);
      setNotice(modal === "edit" ? "Employee updated successfully." : "Employee added successfully.");
      await loadEmployees();
    } catch (saveError) {
      setError(saveError.message || "Unable to save employee.");
    } finally {
      setIsSaving(false);
    }
  }

  async function showDetails(id) {
    try {
      setSelected(await getEmployee(id));
      setModal("details");
    } catch (loadError) {
      setError(loadError.message || "Unable to load employee details.");
    }
  }

  async function removeEmployee(employee) {
    if (!window.confirm(`Delete employee "${employee.full_name}"? This cannot be undone.`)) return;
    try {
      await deleteEmployee(employee.id);
      setNotice("Employee deleted successfully.");
      if (result.items.length === 1 && page > 1) setPage((current) => current - 1);
      else await loadEmployees();
    } catch (deleteError) {
      setError(deleteError.message || "Unable to delete employee.");
    }
  }

  const totalPages = Math.max(1, Math.ceil(result.total / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">People register</p><h2 className="mt-1 text-2xl font-bold text-ink">Employee Management</h2><p className="mt-1 text-sm text-muted">Manage employee records and employment details.</p></div>
        <button className="inline-flex items-center justify-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#126C88]" onClick={() => { setSelected(null); setModal("add"); }} type="button"><Plus size={17} /> Add Employee</button>
      </div>
      {notice && <div className="flex items-center justify-between rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"><span>{notice}</span><button onClick={() => setNotice("")} type="button">Dismiss</button></div>}
      {error && <div className="flex items-center justify-between rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"><span>{error}</span><button onClick={() => setError("")} type="button">Dismiss</button></div>}

      <section className="rounded-2xl border border-border bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-50 text-sidebar"><Users size={21} /></span><div><p className="text-sm text-muted">Total employees</p><p className="text-2xl font-bold text-ink">{result.total}</p></div></div>
          <label className="flex w-full items-center rounded-xl border border-border bg-canvas px-3 md:max-w-sm"><Search className="text-muted" size={18} /><input className="w-full bg-transparent px-2 py-3 text-sm text-ink outline-none placeholder:text-muted" onChange={(event) => setSearch(event.target.value)} placeholder="Search loaded employees" value={search} /></label>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
        {isLoading ? <TableLoading /> : visibleEmployees.length ? <EmployeeTable employees={visibleEmployees} onDelete={removeEmployee} onEdit={(employee) => { setSelected(employee); setModal("edit"); }} onView={showDetails} /> : <div className="p-12 text-center text-sm text-muted">{search ? "No employees match your search on this page." : "No employees have been added yet."}</div>}
        <div className="flex flex-col justify-between gap-3 border-t border-border px-5 py-4 text-sm text-muted sm:flex-row sm:items-center"><span>Showing {visibleEmployees.length} of {result.total} records</span><div className="flex items-center gap-2"><button aria-label="Previous page" className="rounded-lg border border-border p-2 hover:bg-canvas disabled:opacity-40" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button"><ChevronLeft size={17} /></button><span>Page {page} of {totalPages}</span><button aria-label="Next page" className="rounded-lg border border-border p-2 hover:bg-canvas disabled:opacity-40" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)} type="button"><ChevronRight size={17} /></button></div></div>
      </section>
      {modal === "add" || modal === "edit" ? <EmployeeForm employee={modal === "edit" ? selected : null} error={error} isSaving={isSaving} onClose={() => { setModal(null); setError(""); }} onSubmit={saveEmployee} /> : null}
      {modal === "details" ? <EmployeeDetails employee={selected} onClose={() => { setModal(null); setSelected(null); }} /> : null}
    </div>
  );
}

function EmployeeTable({ employees, onDelete, onEdit, onView }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[780px] text-left text-sm"><thead className="bg-canvas text-xs uppercase tracking-wide text-muted"><tr><th className="px-5 py-4 font-semibold">ID</th><th className="px-5 py-4 font-semibold">Employee</th><th className="px-5 py-4 font-semibold">Department</th><th className="px-5 py-4 font-semibold">Designation</th><th className="px-5 py-4 font-semibold">Branch</th><th className="px-5 py-4 font-semibold">Status</th><th className="px-5 py-4 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-border">{employees.map((employee) => <tr className="hover:bg-canvas/60" key={employee.id}><td className="px-5 py-4 font-semibold text-muted">#{employee.id}</td><td className="px-5 py-4"><p className="font-semibold text-ink">{employee.full_name}</p><p className="text-xs text-muted">{employee.employee_code}</p></td><td className="px-5 py-4 text-muted">{employee.department || "—"}</td><td className="px-5 py-4 text-muted">{employee.designation || "—"}</td><td className="px-5 py-4 text-muted">{employee.branch || "—"}</td><td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${employee.employment_status === "Active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{employee.employment_status}</span></td><td className="px-5 py-4"><div className="flex justify-end gap-1"><IconButton label="View employee" onClick={() => onView(employee.id)}><Eye size={16} /></IconButton><IconButton label="Edit employee" onClick={() => onEdit(employee)}><Pencil size={16} /></IconButton><IconButton label="Delete employee" onClick={() => onDelete(employee)}><Trash2 className="text-red-500" size={16} /></IconButton></div></td></tr>)}</tbody></table></div>;
}

function IconButton({ children, label, onClick }) {
  return <button aria-label={label} className="rounded-lg p-2 text-muted hover:bg-canvas hover:text-ink" onClick={onClick} type="button">{children}</button>;
}

function TableLoading() {
  return <div className="space-y-3 p-5">{Array.from({ length: 5 }, (_, index) => <div className="h-12 animate-pulse rounded-lg bg-canvas" key={index} />)}</div>;
}
