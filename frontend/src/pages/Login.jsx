import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const registrationMessage = location.state?.message;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (!username.trim() || !password) {
      setError("Enter your email and password to continue.");
      return;
    }
    setIsSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch (loginError) {
      setError(loginError.message || "Unable to sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-sidebar via-[#08749A] to-accent px-4 py-8">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl bg-white shadow-2xl lg:grid-cols-[1fr_0.9fr]">
        <section className="hidden flex-col justify-between bg-sidebar p-10 text-white lg:flex">
          <Logo />
          <div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-cyan-100/70">
              Intelligent records
            </p>
            <h1 className="max-w-md text-4xl font-bold leading-tight">
              Bring every register into one trusted workspace.
            </h1>
            <p className="mt-5 max-w-md text-sm leading-6 text-cyan-50/70">
              Securely manage business records, review digitized documents, and
              keep your teams aligned with SmartLedger.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-cyan-100/60">
            <ShieldCheck size={16} />
            Secure role-based access
          </div>
        </section>

        <section className="p-6 sm:p-10">
          <div className="mb-8 lg:hidden">
            <div className="rounded-2xl bg-sidebar p-4">
              <Logo />
            </div>
          </div>
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">
              Welcome back
            </p>
            <h2 className="mt-2 text-3xl font-bold text-ink">Sign in to SmartLedger</h2>
            <p className="mt-2 text-sm text-muted">
              Use your registered account to access the workspace.
            </p>
            {registrationMessage && (
              <p className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-700">
                {registrationMessage}
              </p>
            )}
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-ink">Email address</span>
              <span className="flex items-center rounded-xl border border-border bg-canvas px-3 focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20">
                <Mail className="text-muted" size={18} />
                <input
                  autoComplete="email"
                  className="w-full bg-transparent px-3 py-3 text-sm text-ink outline-none"
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="you@company.com"
                  type="email"
                  value={username}
                />
              </span>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-ink">Password</span>
              <span className="flex items-center rounded-xl border border-border bg-canvas px-3 focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20">
                <LockKeyhole className="text-muted" size={18} />
                <input
                  autoComplete="current-password"
                  className="w-full bg-transparent px-3 py-3 text-sm text-ink outline-none"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                />
                <button
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="p-1 text-muted hover:text-ink"
                  onClick={() => setShowPassword((visible) => !visible)}
                  type="button"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>
            {error && (
              <p className="rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-700">
                {error}
              </p>
            )}
            <button
              className="flex w-full items-center justify-center rounded-xl bg-sidebar px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-sidebar/20 transition hover:bg-[#126C88] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? (
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              ) : (
                "Sign in"
              )}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-muted">Need access? Contact your SmartLedger administrator.</p>
        </section>
      </div>
    </main>
  );
}
