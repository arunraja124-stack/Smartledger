import api from "./api";

export async function getDashboardData() {
  const [summary, attendance, analytics, lowStock] = await Promise.all([
    api.get("/dashboard/summary"),
    api.get("/dashboard/attendance"),
    api.get("/dashboard/analytics"),
    api.get("/dashboard/low-stock"),
  ]);

  return {
    summary: summary.data,
    attendance: attendance.data,
    analytics: analytics.data,
    lowStock: lowStock.data,
  };
}
