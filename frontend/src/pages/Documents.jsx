import { CheckCircle, Download, Pencil, Play, Save, Trash2, UploadCloud, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  approveDocument,
  deleteReview,
  downloadDocument,
  getReview,
  insertApproved,
  listDocuments,
  processDocument,
  retryDocument,
  updateReview,
  uploadDocument,
} from "../services/documentService";
import { listEmployees } from "../services/employeeService";

const registerTypes = [
  ["employees", "Employees"],
  ["attendance", "Attendance"],
  ["visitors", "Visitors"],
  ["suppliers", "Suppliers"],
  ["spare_parts", "Spare parts"],
  ["purchases", "Purchases"],
  ["spare_sales", "Spare sales"],
  ["customer_enquiries", "Customer enquiries"],
];
const purchaseFields = [
  ["invoice_number", "Invoice number"],
  ["supplier_name", "Supplier name"],
  ["spare_part", "Spare part"],
  ["quantity", "Quantity"],
  ["unit_price", "Unit price"],
  ["total_amount", "Total amount"],
  ["purchase_date", "Purchase date"],
];
const attendanceFields = [
  ["employee_code", "Employee ID"],
  ["employee_name", "Employee name"],
  ["attendance_date", "Attendance date"],
  ["status", "Status"],
  ["in_time", "In time"],
  ["out_time", "Out time"],
  ["remarks", "Remarks"],
];
const visitorFields = [
  ["visitor_name", "Visitor name"],
  ["visit_date", "Visit date"],
  ["organization", "Organization"],
  ["purpose", "Purpose"],
  ["contact_number", "Contact number"],
  ["time_in", "Time in"],
  ["time_out", "Time out"],
];

function parseData(record) {
  try {
    return JSON.parse(record.extracted_data);
  } catch {
    return {};
  }
}

function isStructuredPurchase(record) {
  const data = parseData(record);
  return Boolean(
    data.invoice_number &&
    data.supplier_name &&
    data.spare_part &&
    Object.prototype.hasOwnProperty.call(data, "quantity") &&
    Object.prototype.hasOwnProperty.call(data, "unit_price") &&
    Object.prototype.hasOwnProperty.call(data, "total_amount"),
  );
}

function isLegacyRawRecord(record) {
  const data = parseData(record);
  return Object.keys(data).length === 1 && typeof data.raw_text === "string" && data.raw_text.trim();
}

function isStructuredAttendance(record) {
  const data = parseData(record);
  return Boolean(data.employee_code || data.employee_name || data.status);
}

function purchaseHasValidationError(record) {
  const data = parseData(record);
  const required = ["purchase_date", "invoice_number", "supplier_name", "spare_part", "quantity", "unit_price", "total_amount"];
  if (required.some((field) => data[field] === undefined || data[field] === "" || data[field] === null)) return true;
  const quantity = Number(data.quantity);
  const unitPrice = Number(data.unit_price);
  const total = Number(data.total_amount);
  return !Number.isFinite(quantity) || quantity <= 0 || !Number.isFinite(unitPrice) || unitPrice < 0 ||
    !Number.isFinite(total) || Math.abs(quantity * unitPrice - total) > 0.01;
}

export default function Documents() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [registerType, setRegisterType] = useState("");
  const [document, setDocument] = useState(null);
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingAttendanceId, setEditingAttendanceId] = useState(null);
  const [editingVisitorId, setEditingVisitorId] = useState(null);
  const [visitorSearch, setVisitorSearch] = useState("");
  const [visitorPage, setVisitorPage] = useState(1);
  const [employees, setEmployees] = useState([]);
  const [documentList, setDocumentList] = useState([]);

  async function restoreDocument(item) {
    setDocument(item);
    setRecords(item.status === "Uploaded" ? [] : await getReview(item.id));
  }

  useEffect(() => {
    let active = true;
    listDocuments()
      .then(async (result) => {
        if (!active) return;
        setDocumentList(result.items || []);
        if (result.items?.length) await restoreDocument(result.items[0]);
      })
      .catch((loadError) => { if (active) setError(loadError.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (registerType !== "attendance" && document?.register_type !== "attendance") return;
    listEmployees(1, 100).then((result) => setEmployees(result.items || [])).catch((loadError) => setError(loadError.message));
  }, [registerType, document?.register_type]);

  async function action(fn, success, updateDocument = true) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await fn();
      if (result && updateDocument) {
        setDocument(result);
        setDocumentList((current) => current.map((item) => item.id === result.id ? result : item));
      }
      if (success) setNotice(typeof success === "function" ? success(result) : success);
      return result;
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setLoading(false);
    }
  }

  async function upload() {
    if (!registerType) return setError("Select the target register.");
    if (!file) return setError("Choose a JPG, JPEG, or PNG image first.");
    await action(async () => {
      const result = await uploadDocument(file, registerType);
      setDocumentList((current) => [result, ...current]);
      setRecords([]);
      setReviewError("");
      return result;
    }, "Document uploaded.");
  }

  async function process() {
    await action(async () => {
      const result = await processDocument(document.id);
      const review = await getReview(document.id);
      if (result.register_type === "purchases") {
        const structured = review.filter(isStructuredPurchase);
        if (structured.length !== review.length || structured.length === 0) {
          setRecords(review);
          setReviewError(
            "This document contains legacy OCR rows. Click Retry OCR to reprocess it with the structured purchase extractor.",
          );
        } else {
          setReviewError("");
          setRecords(structured);
        }
      } else if (result.register_type === "attendance") {
        const structured = review.filter(isStructuredAttendance);
        setReviewError(structured.length
          ? ""
          : "Attendance OCR could not identify employee rows. Review the image and retry.");
        setRecords(structured);
      } else {
        setReviewError("");
        setRecords(review);
      }
      return result;
    }, "OCR processing completed.");
  }

  async function retry() {
    await action(async () => {
      const result = await retryDocument(document.id);
      setRecords(await getReview(document.id));
      setReviewError("");
      return result;
    }, "Legacy OCR records replaced with structured purchase rows.");
  }

  function updateField(recordId, field, value) {
    setRecords((current) => current.map((record) => {
      if (record.id !== recordId) return record;
      const data = parseData(record);
      return { ...record, extracted_data: JSON.stringify({ ...data, [field]: value }) };
    }));
  }

  async function saveRecord(record) {
    if (document?.register_type === "attendance") {
      const prepared = prepareAttendanceRecord(record);
      if (prepared.error) return setError(prepared.error);
      const saved = await action(
        () => updateReview(document.id, record.id, JSON.stringify(prepared.data)),
        "Attendance correction saved.",
        false,
      );
      if (saved) setRecords((current) => current.map((item) => item.id === record.id ? saved : item));
      setEditingAttendanceId(null);
      return;
    }
    if (document?.register_type === "purchases") {
      const data = parseData(record);
      const missing = purchaseFields
        .filter(([field]) => field !== "purchase_date")
        .find(([field]) => data[field] === undefined || data[field] === "");
      if (missing) return setError(`${missing[1]} is required for row ${record.row_number}.`);
    }
    if (document?.register_type === "visitors") {
      const data = parseData(record);
      for (const [field, label] of [["visitor_name", "Visitor name"], ["visit_date", "Visit date"]]) {
        if (!String(data[field] ?? "").trim()) return setError(`${label} is required for row ${record.row_number}.`);
      }
    }

    const saved = await action(
      () => updateReview(document.id, record.id, record.extracted_data),
      "Review record saved.",
      false,
    );
    if (saved) {
      setRecords((current) => current.map((item) => item.id === record.id ? saved : item));
      if (document?.register_type === "visitors") setEditingVisitorId(null);
    }
  }

  function prepareAttendanceRecord(record) {
    const data = parseData(record);
    const employee = employees.find((item) => item.employee_code?.toLowerCase() === data.employee_code?.trim().toLowerCase());
    if (employee && String(employee.full_name || "").trim().toLowerCase() !== String(data.employee_name || "").trim().toLowerCase()) {
      return { error: `Row ${record.row_number}: employee name must match the selected employee.` };
    }
    if (!data.attendance_date || Number.isNaN(Date.parse(data.attendance_date))) {
      return { error: `Row ${record.row_number}: enter a valid attendance date.` };
    }
    if (!["Present", "Absent", "Leave", "Half Day"].includes(data.status)) {
      return { error: `Row ${record.row_number}: select a valid attendance status.` };
    }
    const timePattern = /^(?:[01]\d|2[0-3]):[0-5]\d(?:\s?[AP]M)?$/i;
    if ((data.in_time && !timePattern.test(data.in_time.trim())) || (data.out_time && !timePattern.test(data.out_time.trim()))) {
      return { error: `Row ${record.row_number}: enter valid in/out times.` };
    }
    return {
      data: employee
        ? { ...data, employee_code: employee.employee_code, employee_name: employee.full_name }
        : data,
    };
  }

  async function saveAllAttendance() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const prepared = displayRecords.map((record) => ({ record, ...prepareAttendanceRecord(record) }));
      const invalid = prepared.find((item) => item.error);
      if (invalid) {
        setError(invalid.error);
        return;
      }
      const saved = [];
      for (const item of prepared) {
        saved.push(await updateReview(document.id, item.record.id, JSON.stringify(item.data)));
      }
      setRecords((current) => current.map((record) => saved.find((item) => item.id === record.id) || record));
      setEditingAttendanceId(null);
      setNotice(`${saved.length} attendance rows saved.`);
    } catch (saveError) {
      setError(`Attendance save all stopped: ${saveError.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function removeAttendanceRecord(record) {
    if (!window.confirm(`Delete extracted attendance row ${record.row_number}? This will not delete permanent attendance data.`)) return;
    await action(async () => {
      await deleteReview(document.id, record.id);
      setRecords((current) => current.filter((item) => item.id !== record.id));
      setDocument((current) => current ? { ...current, extracted_row_count: Math.max(0, current.extracted_row_count - 1) } : current);
    }, "Extracted attendance row deleted.", false);
  }

  async function removeVisitorRecord(record) {
    if (!window.confirm(`Delete extracted visitor row ${record.row_number}? This will not delete permanent visitor data.`)) return;
    await action(async () => {
      await deleteReview(document.id, record.id);
      setRecords((current) => current.filter((item) => item.id !== record.id));
      setDocument((current) => current ? { ...current, extracted_row_count: Math.max(0, current.extracted_row_count - 1) } : current);
    }, "Extracted visitor row deleted.", false);
  }

  const isPurchase = document?.register_type === "purchases";
  const isAttendance = document?.register_type === "attendance";
  const isVisitor = document?.register_type === "visitors";
  const visitorFilteredRecords = isVisitor
    ? records.filter((record) => {
      const term = visitorSearch.trim().toLowerCase();
      return !term || Object.values(parseData(record)).some((value) => String(value ?? "").toLowerCase().includes(term));
    })
    : records;
  const displayRecords = isPurchase
    ? records.filter(isStructuredPurchase)
    : isAttendance
      ? records.filter((record) => !isLegacyRawRecord(record))
      : visitorFilteredRecords.slice((visitorPage - 1) * 10, visitorPage * 10);
  const hasUnstructuredPurchaseRecords = isPurchase && records.length > 0 && displayRecords.length === 0;
  const canRetry = isPurchase && records.length > 0 && records.every(isLegacyRawRecord);
  const canApprove = ["Staff", "Manager", "Admin"].includes(user?.role);
  const recordHasValidationError = (record) => {
    if (isPurchase) return purchaseHasValidationError(record);
    if (isAttendance) {
      const data = parseData(record);
      return !data.employee_code || !data.employee_name || !data.attendance_date ||
        !["Present", "Absent", "Leave", "Half Day"].includes(data.status);
    }
    if (isVisitor) {
      const data = parseData(record);
      return !data.visitor_name || !data.visit_date;
    }
    return false;
  };
  const approvalRecords = isVisitor ? visitorFilteredRecords : displayRecords;
  const canApproveDocument = canApprove && document?.status === "Review Required" &&
    approvalRecords.length > 0 && approvalRecords.every((record) => !recordHasValidationError(record));
  const attendanceSummary = isAttendance ? {
    total: displayRecords.length,
    present: displayRecords.filter((record) => parseData(record).status === "Present").length,
    absent: displayRecords.filter((record) => parseData(record).status === "Absent").length,
    halfDay: displayRecords.filter((record) => parseData(record).status === "Half Day").length,
  } : null;
  const canInsert = canApprove && document?.status === "Approved";
  const missingMasterData = /Missing master data|No supplier exists|No spare part exists/.test(error);
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">Intelligent documents</p>
        <h2 className="mt-1 text-2xl font-bold text-ink">Documents & OCR</h2>
        <p className="mt-1 text-sm text-muted">Upload, review, approve, and export OCR records using the backend workflow.</p>
      </div>
      <section className="rounded-2xl border border-border bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <label>
            <span className="mb-2 block text-xs font-semibold uppercase text-muted">Target register</span>
            <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm" onChange={(event) => setRegisterType(event.target.value)} value={registerType}>
              <option value="">Select a register</option>
              {registerTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label>
            <span className="mb-2 block text-xs font-semibold uppercase text-muted">Image file</span>
            <input accept=".jpg,.jpeg,.png,image/jpeg,image/png" className="w-full rounded-xl border border-border bg-canvas px-3 py-2.5 text-sm" onChange={(event) => setFile(event.target.files?.[0] || null)} type="file" />
          </label>
          <button className="inline-flex items-center justify-center gap-2 self-end rounded-xl bg-sidebar px-4 py-3 text-sm font-semibold text-white disabled:opacity-50" disabled={loading || !file || !registerType} onClick={upload} type="button"><UploadCloud size={17} /> Upload</button>
        </div>
        <p className="mt-3 text-xs text-muted">Supported formats: JPG, JPEG, PNG. The backend enforces the file size limit.</p>
      </section>
      {error && <p className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
      {missingMasterData && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">Create the required master records first: <a className="font-semibold underline" href="/suppliers">Suppliers</a> and <a className="font-semibold underline" href="/spare-parts">Spare Parts</a>. Then return here and approve again. No purchase or inventory data was changed.</p>}
      {notice && <p className="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}
      {documentList.length > 0 && <section className="rounded-2xl border border-border bg-white p-5 shadow-sm">
        <label className="block max-w-2xl">
          <span className="mb-2 block text-xs font-semibold uppercase text-muted">Saved OCR documents</span>
          <select className="w-full rounded-xl border border-border bg-canvas px-3 py-3 text-sm" disabled={loading} onChange={(event) => {
            const selected = documentList.find((item) => item.id === Number(event.target.value));
            if (selected) restoreDocument(selected).catch((loadError) => setError(loadError.message));
          }} value={document?.id || ""}>
            {documentList.map((item) => <option key={item.id} value={item.id}>{item.original_filename} · {item.register_type} · {item.status} · {item.extracted_row_count} rows</option>)}
          </select>
        </label>
      </section>}
      {document && (
        <section className="rounded-2xl border border-border bg-white p-5 shadow-sm">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div><p className="font-bold text-ink">{document.original_filename}</p><p className="text-sm text-muted">Target: {document.register_type} · Status: {document.status} · Rows: {document.extracted_row_count}</p></div>
            <div className="flex flex-wrap gap-2">
              {canRetry ? <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold" disabled={loading} onClick={retry} type="button"><Play size={15} /> Retry OCR</button> : <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold" disabled={loading} onClick={process} type="button"><Play size={15} /> Process OCR</button>}
              {canApprove && <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold disabled:opacity-50" disabled={loading || !canApproveDocument} onClick={() => action(() => approveDocument(document.id), "Records approved.")} type="button"><CheckCircle size={15} /> Approve</button>}
              {canApprove && <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold disabled:opacity-50" disabled={loading || !canInsert} onClick={() => action(() => insertApproved(document.id), (result) => `${result?.inserted_row_count ?? 0} ${isVisitor ? "visitor" : "purchase"} records inserted.`)} type="button"><Save size={15} /> Insert</button>}
              {isAttendance && document.status === "Review Required" && <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold disabled:opacity-50" disabled={loading || !displayRecords.length} onClick={saveAllAttendance} type="button"><Save size={15} /> Save all</button>}
              <button className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm font-semibold" onClick={() => action(() => downloadDocument(document.id), "Export downloaded.")} type="button"><Download size={15} /> Excel</button>
            </div>
          </div>
          {!canApprove && <p className="mt-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">A valid authenticated Staff, Manager, or Admin account is required for approval and insertion.</p>}
          {canApprove && document.status === "Review Required" && !canApproveDocument && <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Complete all required fields and correct validation errors before approval.</p>}
          {isAttendance && employees.length === 0 && <p className="mt-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">No employee master records are available. OCR attendance will be stored with employee ID and name snapshots; master records are optional.</p>}
          {attendanceSummary && <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4"><div className="rounded-lg bg-canvas p-3 text-sm">Total <strong>{attendanceSummary.total}</strong></div><div className="rounded-lg bg-canvas p-3 text-sm">Present <strong>{attendanceSummary.present}</strong></div><div className="rounded-lg bg-canvas p-3 text-sm">Absent <strong>{attendanceSummary.absent}</strong></div><div className="rounded-lg bg-canvas p-3 text-sm">Half Day <strong>{attendanceSummary.halfDay}</strong></div></div>}
          {isAttendance && <datalist id="attendance-employees">{employees.map((employee) => <option key={employee.id} value={employee.employee_code}>{employee.full_name}</option>)}</datalist>}
          {document.status === "Inserted" && <p className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{document.approved_row_count} records inserted. <a className="font-semibold underline" href={isVisitor ? "/visitors" : "/purchases"}>Open the {isVisitor ? "Visitors" : "Purchases"} register</a>.</p>}
          {isVisitor && <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><span className="text-sm font-semibold text-ink">Total visitors: {visitorFilteredRecords.length}</span><input className="rounded-lg border border-border bg-white px-3 py-2 text-sm" onChange={(event) => { setVisitorSearch(event.target.value); setVisitorPage(1); }} placeholder="Search visitor rows" value={visitorSearch} /></div>}
          {(reviewError || hasUnstructuredPurchaseRecords) && <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{reviewError || "This document contains legacy unstructured OCR records. Re-upload the image to extract structured purchase rows."}</div>}
          {displayRecords.length ? (
            <div className="mt-5 space-y-3">
              {displayRecords.map((record) => {
                const data = parseData(record);
                const attendanceEditing = isAttendance && editingAttendanceId === record.id;
                const attendanceInvalid = isAttendance && recordHasValidationError(record);
                return (
                  <div className={`rounded-xl border bg-canvas p-4 ${attendanceInvalid ? "border-red-300" : "border-border"}`} key={record.id}>
                    <div className="mb-3 flex items-center justify-between text-xs text-muted"><span>Row {record.row_number} · Confidence {record.confidence == null ? "Not available" : `${record.confidence}%`}</span><span>{record.status}</span></div>
                    {isPurchase ? (
                      <div className="grid gap-3 md:grid-cols-4">
                        {purchaseFields.map(([field, label]) => <label key={field}><span className="mb-1 block text-xs font-semibold text-muted">{label}{field === "purchase_date" && <span className="ml-1 font-normal">(required before approval)</span>}</span><input className={`w-full rounded-lg border bg-white px-3 py-2 text-sm ${record.confidence != null && record.confidence < 70 ? "border-amber-400" : "border-border"}`} onChange={(event) => updateField(record.id, field, event.target.value)} type={field === "purchase_date" ? "date" : "text"} value={data[field] ?? ""} /></label>)}
                      </div>
                    ) : isVisitor ? (
                      <div className="grid gap-3 md:grid-cols-4">
                        {visitorFields.map(([field, label]) => <label key={field}><span className="mb-1 block text-xs font-semibold text-muted">{label}</span><input readOnly={editingVisitorId !== record.id} className={`w-full rounded-lg border bg-white px-3 py-2 text-sm ${recordHasValidationError(record) ? "border-red-300" : "border-border"}`} onChange={(event) => updateField(record.id, field, event.target.value)} type={field === "visit_date" ? "date" : "text"} value={data[field] ?? ""} /></label>)}
                      </div>
                    ) : isAttendance ? (
                      <div className="grid gap-3 md:grid-cols-4">
                        {attendanceFields.map(([field, label]) => <label key={field}><span className="mb-1 block text-xs font-semibold text-muted">{label}</span>{field === "status" && attendanceEditing ? <select className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm" onChange={(event) => updateField(record.id, field, event.target.value)} value={data[field] ?? ""}><option value="">Select status</option>{["Present", "Absent", "Leave", "Half Day"].map((status) => <option key={status}>{status}</option>)}</select> : <input list={field === "employee_code" && employees.length ? "attendance-employees" : undefined} readOnly={!attendanceEditing} className={`w-full rounded-lg border bg-white px-3 py-2 text-sm ${attendanceInvalid ? "border-red-300" : "border-border"}`} onChange={(event) => { updateField(record.id, field, event.target.value); if (field === "employee_code") { const employee = employees.find((item) => item.employee_code?.toLowerCase() === event.target.value.toLowerCase()); if (employee) updateField(record.id, "employee_name", employee.full_name); } }} type={field === "attendance_date" ? "date" : "text"} value={data[field] ?? ""} />}</label>)}
                      </div>
                    ) : <textarea className="min-h-24 w-full rounded-lg border border-border bg-white p-3 text-sm" onChange={(event) => setRecords((current) => current.map((item) => item.id === record.id ? { ...item, extracted_data: event.target.value } : item))} value={record.extracted_data} />}
                    {isPurchase && data.extraction_warnings?.length > 0 && <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">Warnings: {data.extraction_warnings.join("; ")}</p>}
                    {attendanceInvalid && <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">This row needs correction. Confirm the employee ID exists in the Employees master list.</p>}
                    {isAttendance || isVisitor ? <div className="mt-3 flex gap-2"><button className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-semibold disabled:opacity-50" disabled={document.status !== "Review Required" || loading} onClick={() => isAttendance ? (attendanceEditing ? saveRecord(record) : setEditingAttendanceId(record.id)) : (editingVisitorId === record.id ? saveRecord(record) : setEditingVisitorId(record.id))} type="button">{(isAttendance ? attendanceEditing : editingVisitorId === record.id) ? <><Save size={14} /> Save</> : <><Pencil size={14} /> Edit</>}</button>{(isAttendance ? attendanceEditing : editingVisitorId === record.id) && <button className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-semibold" onClick={() => isAttendance ? setEditingAttendanceId(null) : setEditingVisitorId(null)} type="button"><X size={14} /> Cancel</button>}<button className="inline-flex items-center gap-2 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 disabled:opacity-50" disabled={document.status !== "Review Required" || loading} onClick={() => isAttendance ? removeAttendanceRecord(record) : removeVisitorRecord(record)} type="button"><Trash2 size={14} /> Delete</button></div> : <button className="mt-3 inline-flex items-center gap-2 rounded-lg bg-sidebar px-3 py-2 text-xs font-semibold text-white disabled:opacity-50" disabled={document.status !== "Review Required" || loading} onClick={() => saveRecord(record)} type="button"><Save size={14} /> Save correction</button>}
                    {record.validation_error && <p className="mt-2 text-xs text-red-700">{record.validation_error}</p>}
                  </div>
                );
              })}
              {isVisitor && visitorFilteredRecords.length > 10 && <div className="flex items-center justify-between pt-2 text-sm text-muted"><span>Page {visitorPage} of {Math.ceil(visitorFilteredRecords.length / 10)}</span><div className="flex gap-2"><button className="rounded-lg border border-border px-3 py-1 disabled:opacity-50" disabled={visitorPage === 1} onClick={() => setVisitorPage((page) => page - 1)} type="button">Previous</button><button className="rounded-lg border border-border px-3 py-1 disabled:opacity-50" disabled={visitorPage >= Math.ceil(visitorFilteredRecords.length / 10)} onClick={() => setVisitorPage((page) => page + 1)} type="button">Next</button></div></div>}
            </div>
          ) : !reviewError && !hasUnstructuredPurchaseRecords && <div className="mt-5 rounded-xl bg-canvas p-8 text-center text-sm text-muted">Process the upload to review extracted records.</div>}
        </section>
      )}
    </div>
  );
}
