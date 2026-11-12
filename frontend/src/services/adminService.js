import api from "./api";

export async function listUsers(page = 1, pageSize = 25) { const response = await api.get("/users", { params: { page, page_size: pageSize } }); return response.data; }
export async function createUser(payload) { const response = await api.post("/users", payload); return response.data; }
export async function updateUser(id, payload) { const response = await api.patch(`/users/${id}`, payload); return response.data; }
export async function resetUserPassword(id, password) { const response = await api.post(`/users/${id}/reset-password`, password ? { password } : {}); return response.data; }
