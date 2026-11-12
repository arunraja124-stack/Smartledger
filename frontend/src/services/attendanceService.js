import api from "./api";

export async function listAttendance(page = 1, pageSize = 10) {
  const response = await api.get("/attendance", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function getAttendance(id) {
  const response = await api.get(`/attendance/${id}`);
  return response.data;
}

export async function createAttendance(payload) {
  const response = await api.post("/attendance", payload);
  return response.data;
}

export async function updateAttendance(id, payload) {
  const response = await api.put(`/attendance/${id}`, payload);
  return response.data;
}

export async function deleteAttendance(id) {
  await api.delete(`/attendance/${id}`);
}
