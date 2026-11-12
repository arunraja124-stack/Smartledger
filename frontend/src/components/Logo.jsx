import { BookOpenCheck } from "lucide-react";

export default function Logo({ compact = false }) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-sidebar shadow-sm">
        <BookOpenCheck size={22} strokeWidth={2.2} />
      </span>
      {!compact && (
        <span>
          <span className="block text-lg font-bold tracking-tight text-white">
            SmartLedger
          </span>
          <span className="block text-[10px] font-medium uppercase tracking-[0.18em] text-cyan-100/70">
            Digital registers
          </span>
        </span>
      )}
    </div>
  );
}
