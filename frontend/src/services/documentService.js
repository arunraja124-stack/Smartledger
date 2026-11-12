import api from "./api";

export async function uploadDocument(file, registerType, onUploadProgress) {
  const body = new FormData();
  body.append("file", file);
  body.append("register_type", registerType);
  const response = await api.post("/documents/upload", body, { onUploadProgress });
  return response.data;
}
export async function listDocuments(page = 1, pageSize = 25) { const response = await api.get("/documents", { params: { page, page_size: pageSize } }); return response.data; }
export async function processDocument(id) { const response = await api.post(`/documents/${id}/process`); return response.data; }
export async function retryDocument(id) { const response = await api.post(`/documents/${id}/retry`); return response.data; }
export async function getReview(id) { const response = await api.get(`/documents/${id}/review`); return response.data; }
export async function updateReview(id, recordId, extractedData, status = "Review Required") { const response = await api.put(`/documents/${id}/review/${recordId}`, { extracted_data: extractedData, status }); return response.data; }
export async function deleteReview(id, recordId) { await api.delete(`/documents/${id}/review/${recordId}`); }
export async function approveDocument(id) { const response = await api.post(`/documents/${id}/approve`); return response.data; }
export async function insertApproved(id) { const response = await api.post(`/documents/${id}/insert-approved`); return response.data; }
export async function downloadDocument(id) { const response = await api.get(`/documents/${id}/export`, { responseType: "blob" }); const url = URL.createObjectURL(response.data); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `document-${id}.xlsx`; anchor.click(); URL.revokeObjectURL(url); }
