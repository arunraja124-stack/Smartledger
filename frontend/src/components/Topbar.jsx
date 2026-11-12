import { Bell, Menu, Search } from "lucide-react";
import { useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Topbar({ onMenuClick }) {
  const { user } = useAuth();
  const location = useLocation();
  const title =
    location.pathname.split("/").filter(Boolean)[0]?.replaceAll("-", " ") ||
    "dashboard";

  return (
    <header className="flex min-h-20 items-center justify-between gap-4 border-b border-border bg-white px-4 py-3 sm:px-7">
      <div className="flex min-w-0 items-center gap-3">
        <button
          aria-label="Open navigation"
          className="rounded-xl p-2 text-ink hover:bg-canvas lg:hidden"
          onClick={onMenuClick}
          type="button"
        >
          <Menu size={22} />
        </button>
        <div className="min-w-0">
          <p className="hidden text-xs font-medium capitalize text-muted sm:block">
            SmartLedger / Workspace
          </p>
          <h1 className="truncate text-xl font-bold capitalize text-ink">{title}</h1>
        </div>
      </div>
      <div className="hidden max-w-xs flex-1 items-center rounded-xl border border-border bg-canvas px-3 py-2 md:flex">
        <Search className="text-muted" size={18} />
        <input
          aria-label="Search"
          className="w-full border-0 bg-transparent px-2 text-sm text-ink outline-none placeholder:text-muted"
          placeholder="Search workspace"
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          aria-label="Notifications"
          className="rounded-xl p-2 text-muted hover:bg-canvas hover:text-ink"
          type="button"
        >
          <Bell size={20} />
        </button>
        <div className="hidden text-right sm:block">
          <p className="text-sm font-semibold text-ink">{user?.full_name}</p>
          <p className="text-xs capitalize text-muted">{user?.role?.toLowerCase()}</p>
        </div>
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-sidebar font-bold text-white">
          {user?.full_name?.charAt(0).toUpperCase() || "U"}
        </span>
      </div>
    </header>
  );
}
