import api from "./api";

export async function getReport(type, startDate, endDate) {
  const response = await api.get(`/reports/${type}`, { params: { start_date: startDate || undefined, end_date: endDate || undefined } });
  return response.data;
}

export async function downloadReport(type, startDate, endDate) {
  const response = await api.get(`/reports/${type}/export`, { responseType: "blob", params: { start_date: startDate || undefined, end_date: endDate || undefined } });
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${type}.xlsx`;
  anchor.click();
  URL.revokeObjectURL(url);
}
export async function downloadReportPdf(type, startDate, endDate) {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const response = await api.get(`/reports/${type}/pdf?${params.toString()}`, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${type}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
