import {
  BarChart3,
  BookOpen,
  Boxes,
  ClipboardCheck,
  FileSpreadsheet,
  FileText,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  PackageOpen,
  Settings,
  ShoppingCart,
  Truck,
  UserCog,
  Users,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";

const navigation = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Employees", to: "/employees", icon: Users },
  { label: "Attendance", to: "/attendance", icon: ClipboardCheck },
  { label: "Visitors", to: "/visitors", icon: BookOpen },
  { label: "Suppliers", to: "/suppliers", icon: Truck },
  { label: "Spare Parts", to: "/spare-parts", icon: Boxes },
  { label: "Purchases", to: "/purchases", icon: ShoppingCart },
  { label: "Spare Sales", to: "/spare-sales", icon: PackageOpen },
  { label: "Customer Enquiries", to: "/customer-enquiries", icon: HelpCircle },
  { label: "Documents & OCR", to: "/documents", icon: FileText },
  { label: "Reports", to: "/reports", icon: BarChart3 },
];

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "Admin";

  return (
    <>
      {isOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
          onClick={onClose}
          type="button"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen w-72 flex-col overflow-hidden bg-sidebar px-4 py-5 text-white shadow-xl transition-transform lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-2">
          <Logo />
          <button
            aria-label="Close navigation"
            className="rounded-lg p-2 text-cyan-100 hover:bg-white/10 lg:hidden"
            onClick={onClose}
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mt-8 flex-1 space-y-1 overflow-y-auto pr-1">
          <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-cyan-100/50">
            Main workspace
          </p>
          {navigation.filter(({ to }) => to !== "/reports" || isAdmin).map(({ label, to, icon: Icon }) => (
            <NavLink
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-accent text-sidebar shadow-sm"
                    : "text-cyan-50/80 hover:bg-white/10 hover:text-white"
                }`
              }
              key={to}
              onClick={onClose}
              to={to}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
          {isAdmin && (
            <>
              <p className="px-3 pb-2 pt-6 text-[10px] font-bold uppercase tracking-[0.18em] text-cyan-100/50">
                Administration
              </p>
              <NavLink
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-accent text-sidebar shadow-sm"
                      : "text-cyan-50/80 hover:bg-white/10 hover:text-white"
                  }`
                }
                onClick={onClose}
                to="/users"
              >
                <UserCog size={18} />
                User Management
              </NavLink>
            </>
          )}
        </div>

        <div className="border-t border-white/10 pt-4">
          <div className="mb-3 flex items-center gap-3 rounded-xl bg-white/10 p-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent font-bold text-sidebar">
              {user?.full_name?.charAt(0).toUpperCase() || "U"}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user?.full_name}</p>
              <p className="text-xs text-cyan-100/60">{user?.role}</p>
            </div>
          </div>
          <button
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-cyan-50/80 hover:bg-white/10 hover:text-white"
            onClick={logout}
            type="button"
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
