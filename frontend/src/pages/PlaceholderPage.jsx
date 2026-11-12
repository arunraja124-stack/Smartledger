export default function PlaceholderPage({ title, description }) {
  return (
    <section className="rounded-2xl border border-border bg-white p-6 shadow-sm sm:p-8">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">
        SmartLedger workspace
      </p>
      <h2 className="mt-2 text-2xl font-bold capitalize text-ink">{title}</h2>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{description}</p>
    </section>
  );
}
