import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL;
  if (mode === "production") {
    if (!apiBaseUrl) {
      throw new Error("Set VITE_API_BASE_URL to the deployed HTTPS API before building for production.");
    }
    const apiUrl = new URL(apiBaseUrl);
    if (apiUrl.protocol !== "https:" || ["localhost", "127.0.0.1"].includes(apiUrl.hostname)) {
      throw new Error("Production VITE_API_BASE_URL must use HTTPS and cannot point to localhost.");
    }
  }

  return {
    plugins: [react()],
  };
});
