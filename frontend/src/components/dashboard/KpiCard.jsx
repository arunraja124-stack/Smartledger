export default function KpiCard({ label, value, detail, icon: Icon, tone }) {
  return (
    <article className="rounded-2xl border border-border bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-muted">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-ink">{value}</p>
        </div>
        <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${tone}`}>
          <Icon size={21} />
        </span>
      </div>
      <p className="mt-4 text-xs text-muted">{detail}</p>
    </article>
  );
}
