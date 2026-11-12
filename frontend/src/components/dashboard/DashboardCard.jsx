export default function DashboardCard({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`rounded-2xl border border-border bg-white p-5 shadow-sm ${className}`}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-ink">{title}</h2>
          {subtitle && <p className="mt-1 text-xs text-muted">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
