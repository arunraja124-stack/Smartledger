import api from "./api";

export async function listRegister(resource, page = 1, pageSize = 10) {
  const response = await api.get(`/${resource}`, { params: { page, page_size: pageSize } });
  return response.data;
}

export async function getRegister(resource, id) {
  const response = await api.get(`/${resource}/${id}`);
  return response.data;
}

export async function createRegister(resource, payload) {
  const response = await api.post(`/${resource}`, payload);
  return response.data;
}

export async function updateRegister(resource, id, payload) {
  const response = await api.put(`/${resource}/${id}`, payload);
  return response.data;
}

export async function deleteRegister(resource, id) {
  await api.delete(`/${resource}/${id}`);
}
