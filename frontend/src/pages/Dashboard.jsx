import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  ClipboardCheck,
  FileUp,
  HelpCircle,
  Package,
  RefreshCw,
  ShoppingBag,
  Truck,
  UserPlus,
  Users,
  UsersRound,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import DashboardCard from "../components/dashboard/DashboardCard";
import KpiCard from "../components/dashboard/KpiCard";
import { getDashboardData } from "../services/dashboardService";

const colors = {
  accent: "#16B6B0",
  sidebar: "#075477",
  warning: "#F59E0B",
  absent: "#F87171",
  grid: "#DCECEF",
  muted: "#738A98",
};

const formatNumber = (value) => new Intl.NumberFormat().format(Number(value || 0));
const formatCurrency = (value) =>
  new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(Number(value || 0));

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      setData(await getDashboardData());
    } catch (loadError) {
      setError(loadError.message || "Unable to load dashboard data.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (isLoading) return <DashboardLoading />;
  if (error) {
    return (
      <section className="rounded-2xl border border-red-100 bg-white p-8 text-center shadow-sm">
        <AlertTriangle className="mx-auto text-red-500" size={30} />
        <h2 className="mt-3 text-lg font-bold text-ink">Dashboard unavailable</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">{error}</p>
        <button
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#126C88]"
          onClick={loadDashboard}
          type="button"
        >
          <RefreshCw size={16} />
          Try again
        </button>
      </section>
    );
  }

  const { summary, attendance, analytics, lowStock } = data;
  const attendanceChart = buildAttendanceChart(attendance);
  const enquiryChart = analytics.enquiries_by_status || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            Overview
          </p>
          <h2 className="mt-1 text-2xl font-bold text-ink">Good to see you</h2>
          <p className="mt-1 text-sm text-muted">Here is your live SmartLedger workspace summary.</p>
        </div>
        <button
          className="inline-flex items-center gap-2 self-start rounded-xl border border-border bg-white px-4 py-2.5 text-sm font-semibold text-ink hover:border-accent sm:self-auto"
          onClick={loadDashboard}
          type="button"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard detail="Registered in the system" icon={UsersRound} label="Total Employees" tone="bg-cyan-50 text-sidebar" value={formatNumber(summary.total_employees)} />
        <KpiCard detail={`${formatNumber(summary.absent_today)} absent today`} icon={ClipboardCheck} label="Today's Attendance" tone="bg-emerald-50 text-emerald-700" value={formatNumber(summary.present_today)} />
        <KpiCard detail="All recorded visits" icon={Users} label="Total Visitors" tone="bg-violet-50 text-violet-700" value={formatNumber(summary.total_visitors)} />
        <KpiCard detail="Active supplier register" icon={Truck} label="Total Suppliers" tone="bg-orange-50 text-orange-700" value={formatNumber(summary.total_suppliers)} />
        <KpiCard detail={`${formatNumber(summary.low_stock_items)} need restocking`} icon={Package} label="Spare Parts" tone="bg-blue-50 text-blue-700" value={formatNumber(summary.total_spare_parts)} />
        <KpiCard detail="Across all enquiry statuses" icon={HelpCircle} label="Customer Enquiries" tone="bg-pink-50 text-pink-700" value={formatNumber(summary.customer_enquiries)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <DashboardCard
          subtitle="Recorded attendance grouped by day and status"
          title="Attendance analytics"
        >
          {attendanceChart.length ? (
            <div className="h-72 w-full">
              <ResponsiveContainer>
                <BarChart data={attendanceChart} margin={{ left: -20, right: 8 }}>
                  <CartesianGrid stroke={colors.grid} strokeDasharray="3 3" vertical={false} />
                  <XAxis axisLine={false} dataKey="date" tick={{ fill: colors.muted, fontSize: 11 }} tickLine={false} />
                  <YAxis allowDecimals={false} axisLine={false} tick={{ fill: colors.muted, fontSize: 11 }} tickLine={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Present" fill={colors.accent} radius={[5, 5, 0, 0]} />
                  <Bar dataKey="Absent" fill={colors.absent} radius={[5, 5, 0, 0]} />
                  <Bar dataKey="Leave" fill={colors.warning} radius={[5, 5, 0, 0]} />
                  <Bar dataKey="Half Day" fill={colors.sidebar} radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No attendance records are available yet." />
          )}
        </DashboardCard>

        <DashboardCard
          subtitle="Current distribution by enquiry status"
          title="Customer enquiries"
        >
          {enquiryChart.length ? (
            <div className="h-72 w-full">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={enquiryChart} dataKey="count" nameKey="status" innerRadius={62} outerRadius={92} paddingAngle={3}>
                    {enquiryChart.map((entry, index) => (
                      <Cell fill={[colors.accent, colors.sidebar, colors.warning, "#8B5CF6", "#F87171"][index % 5]} key={entry.status} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No customer enquiry records are available yet." />
          )}
        </DashboardCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <DashboardCard
          action={<Link className="text-xs font-semibold text-sidebar hover:text-accent" to="/spare-parts">View register</Link>}
          subtitle="Items at or below their minimum stock level"
          title="Low-stock alerts"
        >
          {lowStock.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[440px] text-left text-sm">
                <thead className="border-b border-border text-xs uppercase tracking-wide text-muted">
                  <tr><th className="pb-3 font-semibold">Spare part</th><th className="pb-3 font-semibold">Current stock</th><th className="pb-3 font-semibold">Minimum</th><th className="pb-3 text-right font-semibold">Status</th></tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {lowStock.map((part) => (
                    <tr key={part.id}>
                      <td className="py-3"><p className="font-semibold text-ink">{part.part_name}</p><p className="text-xs text-muted">{part.part_code}</p></td>
                      <td className="py-3 font-semibold text-red-600">{formatNumber(part.available_quantity)}</td>
                      <td className="py-3 text-muted">{formatNumber(part.minimum_stock_level)}</td>
                      <td className="py-3 text-right"><span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700"><AlertTriangle size={13} /> Restock</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="Inventory levels are currently healthy." />
          )}
        </DashboardCard>

        <DashboardCard subtitle="Live totals from recorded transactions" title="Financial summary">
          <div className="space-y-4">
            <MetricRow label="Total purchases" value={formatCurrency(analytics.purchase_total)} />
            <MetricRow label="Total spare sales" value={formatCurrency(analytics.sales_total)} />
            <MetricRow label="Purchase value" value={formatCurrency(summary.total_purchases)} />
            <MetricRow label="Sales value" value={formatCurrency(summary.total_sales)} />
          </div>
        </DashboardCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <DashboardCard title="Quick actions" subtitle="Jump directly to common workflows">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <QuickAction icon={UserPlus} label="Add Employee" to="/employees" />
            <QuickAction icon={ClipboardCheck} label="Mark Attendance" to="/attendance" />
            <QuickAction icon={Users} label="Register Visitor" to="/visitors" />
            <QuickAction icon={Truck} label="Add Supplier" to="/suppliers" />
            <QuickAction icon={Package} label="Add Spare Part" to="/spare-parts" />
            <QuickAction icon={FileUp} label="Upload Document" to="/documents" />
          </div>
        </DashboardCard>
        <DashboardCard title="Recent activity" subtitle="Activity feed will appear when a backend activity endpoint is available">
          <EmptyState message="No recent activity endpoint is currently available." icon={BarChart3} />
        </DashboardCard>
      </div>
    </div>
  );
}

function buildAttendanceChart(rows) {
  const grouped = new Map();
  rows.forEach(({ date, status, count }) => {
    const key = String(date).slice(0, 10);
    if (!grouped.has(key)) grouped.set(key, { date: key });
    grouped.get(key)[status] = Number(count);
  });
  return [...grouped.values()];
}

function MetricRow({ label, value }) {
  return <div className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0"><span className="text-sm text-muted">{label}</span><span className="font-bold text-ink">{value}</span></div>;
}

function QuickAction({ icon: Icon, label, to }) {
  return <Link className="group rounded-xl border border-border p-3 transition hover:border-accent hover:bg-canvas" to={to}><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 text-sidebar"><Icon size={17} /></span><span className="mt-2 block text-xs font-semibold text-ink">{label}</span><ArrowUpRight className="mt-2 text-muted transition group-hover:text-accent" size={15} /></Link>;
}

function EmptyState({ message, icon: Icon = ShoppingBag }) {
  return <div className="flex min-h-40 flex-col items-center justify-center rounded-xl bg-canvas px-4 text-center"><Icon className="text-muted" size={25} /><p className="mt-3 text-sm text-muted">{message}</p></div>;
}

function DashboardLoading() {
  return <div className="animate-pulse space-y-6"><div className="h-16 w-72 rounded-xl bg-white/70" /><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, index) => <div className="h-36 rounded-2xl bg-white/70" key={index} />)}</div><div className="grid gap-6 xl:grid-cols-2"><div className="h-80 rounded-2xl bg-white/70" /><div className="h-80 rounded-2xl bg-white/70" /></div></div>;
}
