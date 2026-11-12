import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
  headers: {
    Accept: "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("smartledger_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem("smartledger_access_token");
      window.dispatchEvent(new Event("smartledger:unauthorized"));
    }

    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    const validationMessage = Array.isArray(detail)
      ? detail
          .map((item) => item.msg)
          .filter(Boolean)
          .join(", ")
      : null;
    const message =
      typeof detail === "string"
        ? detail
        : validationMessage ||
          (status === 422
            ? "Please check the submitted fields."
            : status >= 500
              ? "The SmartLedger API encountered a server error."
              : status
                ? `Request failed with status ${status}`
                : "Unable to reach the SmartLedger API");
    const normalized = new Error(message);
    normalized.status = status;
    normalized.response = error.response;
    return Promise.reject(normalized);
  },
);

export default api;
