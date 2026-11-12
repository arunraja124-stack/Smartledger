import { CalendarDays, ChevronLeft, ChevronRight, Eye, Pencil, Plus, Search, Trash2, Users } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import AttendanceDetails from "../components/attendance/AttendanceDetails";
import AttendanceForm from "../components/attendance/AttendanceForm";
import { createAttendance, deleteAttendance, getAttendance, listAttendance, updateAttendance } from "../services/attendanceService";
import { listEmployees } from "../services/employeeService";

const pageSize = 10;

export default function Attendance() {
  const [result, setResult] = useState({ items: [], total: 0, page: 1, page_size: pageSize });
  const [employees, setEmployees] = useState([]);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ date: "", employee: "", status: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isEmployeesLoading, setIsEmployeesLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState(null);
  const [selected, setSelected] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const loadAttendance = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      setResult(await listAttendance(page, pageSize));
    } catch (loadError) {
      setError(loadError.message || "Unable to load attendance records.");
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => { loadAttendance(); }, [loadAttendance]);
  useEffect(() => {
    listEmployees(1, 100)
      .then((response) => setEmployees(response.items))
      .catch((loadError) => setError(loadError.message || "Unable to load employees."))
      .finally(() => setIsEmployeesLoading(false));
  }, []);

  const employeeMap = useMemo(() => new Map(employees.map((employee) => [employee.id, employee])), [employees]);
  const visibleRecords = useMemo(() => result.items.filter((record) =>
    (!filters.date || record.attendance_date === filters.date) &&
    (!filters.employee || String(record.employee_id) === filters.employee || record.employee_code === filters.employee) &&
    (!filters.status || record.status === filters.status),
  ), [filters, result.items]);
  const counts = useMemo(() => ({
    present: visibleRecords.filter((record) => record.status === "Present").length,
    absent: visibleRecords.filter((record) => record.status === "Absent").length,
    halfDay: visibleRecords.filter((record) => record.status === "Half Day").length,
    today: visibleRecords.filter((record) => record.attendance_date === new Date().toISOString().slice(0, 10)).length,
  }), [visibleRecords]);

  function updateFilter(event) {
    setFilters((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function saveRecord(payload) {
    setIsSaving(true);
    setError("");
    try {
      const employee = employees.find((item) => item.id === payload.employee_id);
      if (employee) {
        payload.employee_code = employee.employee_code;
        payload.employee_name = employee.full_name;
      }
      if (modal === "edit") await updateAttendance(selected.id, payload);
      else await createAttendance(payload);
      setModal(null);
      setSelected(null);
      setNotice(modal === "edit" ? "Attendance updated successfully." : "Attendance marked successfully.");
      await loadAttendance();
    } catch (saveError) {
      setError(saveError.message || "Unable to save attendance.");
    } finally {
      setIsSaving(false);
    }
  }

  async function showDetails(id) {
    try {
      setSelected(await getAttendance(id));
      setModal("details");
    } catch (loadError) {
      setError(loadError.message || "Unable to load attendance details.");
    }
  }

  async function removeRecord(record) {
    if (!window.confirm("Delete this attendance record? This cannot be undone.")) return;
    try {
      await deleteAttendance(record.id);
      setNotice("Attendance record deleted successfully.");
      if (result.items.length === 1 && page > 1) setPage((current) => current - 1);
      else await loadAttendance();
    } catch (deleteError) {
      setError(deleteError.message || "Unable to delete attendance record.");
    }
  }

  const totalPages = Math.max(1, Math.ceil(result.total / pageSize));
  const employeeLoadingMessage = isEmployeesLoading ? "Loading employees…" : employees.length ? "" : "No employees available";

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">People register</p><h2 className="mt-1 text-2xl font-bold text-ink">Attendance Management</h2><p className="mt-1 text-sm text-muted">Track daily attendance against the employee register.</p></div>
        <button className="inline-flex items-center justify-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#126C88] disabled:opacity-60" disabled={!employees.length} onClick={() => { setSelected(null); setModal("add"); }} type="button"><Plus size={17} /> Mark Attendance</button>
      </div>
      {notice && <div className="flex items-center justify-between rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"><span>{notice}</span><button onClick={() => setNotice("")} type="button">Dismiss</button></div>}
      {error && <div className="flex items-center justify-between rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"><span>{error}</span><button onClick={() => setError("")} type="button">Dismiss</button></div>}
      {employeeLoadingMessage && <p className="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-800">{employeeLoadingMessage}.</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total records" value={result.total} icon={CalendarDays} />
        <StatCard label="Present on page" value={counts.present} tone="text-emerald-700 bg-emerald-50" icon={Users} />
        <StatCard label="Absent on page" value={counts.absent} tone="text-red-700 bg-red-50" icon={CalendarDays} />
        <StatCard label="Today's records" value={counts.today} tone="text-violet-700 bg-violet-50" icon={CalendarDays} detail={counts.halfDay ? `${counts.halfDay} half-day` : undefined} />
      </div>

      <section className="rounded-2xl border border-border bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2 text-xs text-muted"><Search size={16} /><span>Filters apply to the currently loaded page; the backend currently supports pagination only.</span></div>
        <div className="grid gap-3 md:grid-cols-3">
          <label><span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted">Date</span><input className="w-full rounded-xl border border-border bg-canvas px-3 py-2.5 text-sm text-ink outline-none focus:border-accent" name="date" onChange={updateFilter} type="date" value={filters.date} /></label>
          <label><span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted">Employee</span><select className="w-full rounded-xl border border-border bg-canvas px-3 py-2.5 text-sm text-ink outline-none focus:border-accent" name="employee" onChange={updateFilter} value={filters.employee}><option value="">All employees</option>{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}{result.items.filter((record) => !record.employee_id).map((record) => <option key={`snapshot-${record.id}`} value={record.employee_code}>{record.employee_name} ({record.employee_code})</option>)}</select></label>
          <label><span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted">Status</span><select className="w-full rounded-xl border border-border bg-canvas px-3 py-2.5 text-sm text-ink outline-none focus:border-accent" name="status" onChange={updateFilter} value={filters.status}><option value="">All statuses</option><option>Present</option><option>Absent</option><option>Leave</option><option>Half Day</option></select></label>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
        {isLoading ? <TableLoading /> : visibleRecords.length ? <AttendanceTable employees={employeeMap} records={visibleRecords} onDelete={removeRecord} onEdit={(record) => { setSelected(record); setModal("edit"); }} onView={showDetails} /> : <div className="p-12 text-center text-sm text-muted">{result.total ? "No records match the selected filters on this page." : "No attendance records have been added yet."}</div>}
        <div className="flex flex-col justify-between gap-3 border-t border-border px-5 py-4 text-sm text-muted sm:flex-row sm:items-center"><span>Showing {visibleRecords.length} of {result.total} records</span><div className="flex items-center gap-2"><button aria-label="Previous attendance page" className="rounded-lg border border-border p-2 hover:bg-canvas disabled:opacity-40" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button"><ChevronLeft size={17} /></button><span>Page {page} of {totalPages}</span><button aria-label="Next attendance page" className="rounded-lg border border-border p-2 hover:bg-canvas disabled:opacity-40" onClick={() => setPage((current) => current + 1)} disabled={page >= totalPages} type="button"><ChevronRight size={17} /></button></div></div>
      </section>
      {modal === "add" || modal === "edit" ? <AttendanceForm attendance={modal === "edit" ? selected : null} employees={employees} error={error} isSaving={isSaving} onClose={() => { setModal(null); setError(""); }} onSubmit={saveRecord} /> : null}
      {modal === "details" ? <AttendanceDetails attendance={selected} employeeName={employeeMap.get(selected?.employee_id)?.full_name} onClose={() => { setModal(null); setSelected(null); }} /> : null}
    </div>
  );
}

function StatCard({ detail, icon: Icon, label, tone = "text-sidebar bg-cyan-50", value }) {
  return <article className="rounded-2xl border border-border bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-sm text-muted">{label}</p><p className="mt-2 text-3xl font-bold text-ink">{value}</p>{detail && <p className="mt-1 text-xs text-muted">{detail}</p>}</div><span className={`flex h-11 w-11 items-center justify-center rounded-xl ${tone}`}><Icon size={20} /></span></div></article>;
}

function AttendanceTable({ employees, onDelete, onEdit, onView, records }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[820px] text-left text-sm"><thead className="bg-canvas text-xs uppercase tracking-wide text-muted"><tr><th className="px-5 py-4 font-semibold">ID</th><th className="px-5 py-4 font-semibold">Employee</th><th className="px-5 py-4 font-semibold">Date</th><th className="px-5 py-4 font-semibold">Status</th><th className="px-5 py-4 font-semibold">Check-in</th><th className="px-5 py-4 font-semibold">Check-out</th><th className="px-5 py-4 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-border">{records.map((record) => <tr className="hover:bg-canvas/60" key={record.id}><td className="px-5 py-4 font-semibold text-muted">#{record.id}</td><td className="px-5 py-4 font-semibold text-ink">{record.employee_code} · {record.employee_name || employees.get(record.employee_id)?.full_name || "—"}</td><td className="px-5 py-4 text-muted">{record.attendance_date}</td><td className="px-5 py-4"><StatusBadge status={record.status} /></td><td className="px-5 py-4 text-muted">{record.in_time || "—"}</td><td className="px-5 py-4 text-muted">{record.out_time || "—"}</td><td className="px-5 py-4"><div className="flex justify-end gap-1"><IconButton label="View attendance" onClick={() => onView(record.id)}><Eye size={16} /></IconButton><IconButton label="Edit attendance" onClick={() => onEdit(record)}><Pencil size={16} /></IconButton><IconButton label="Delete attendance" onClick={() => onDelete(record)}><Trash2 className="text-red-500" size={16} /></IconButton></div></td></tr>)}</tbody></table></div>;
}

function StatusBadge({ status }) {
  const styles = { Present: "bg-emerald-50 text-emerald-700", Absent: "bg-red-50 text-red-700", Leave: "bg-amber-50 text-amber-700", "Half Day": "bg-violet-50 text-violet-700" };
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[status] || "bg-slate-100 text-slate-600"}`}>{status}</span>;
}

function IconButton({ children, label, onClick }) {
  return <button aria-label={label} className="rounded-lg p-2 text-muted hover:bg-canvas hover:text-ink" onClick={onClick} type="button">{children}</button>;
}

function TableLoading() {
  return <div className="space-y-3 p-5">{Array.from({ length: 5 }, (_, index) => <div className="h-12 animate-pulse rounded-lg bg-canvas" key={index} />)}</div>;
}
