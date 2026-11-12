import api from "./api";

export async function listEmployees(page = 1, pageSize = 10) {
  const response = await api.get("/employees", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function getEmployee(id) {
  const response = await api.get(`/employees/${id}`);
  return response.data;
}

export async function createEmployee(payload) {
  const response = await api.post("/employees", payload);
  return response.data;
}

export async function updateEmployee(id, payload) {
  const response = await api.put(`/employees/${id}`, payload);
  return response.data;
}

export async function deleteEmployee(id) {
  await api.delete(`/employees/${id}`);
}
