import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import AdminRoute from "./components/AdminRoute";
import { AuthProvider } from "./context/AuthContext";
import AppLayout from "./layouts/AppLayout";
import Login from "./pages/Login";
import PlaceholderPage from "./pages/PlaceholderPage";
import Dashboard from "./pages/Dashboard";
import Employees from "./pages/Employees";
import Attendance from "./pages/Attendance";
import RegisterWorkspace from "./pages/RegisterWorkspace";
import Reports from "./pages/Reports";
import UserManagement from "./pages/UserManagement";
import Documents from "./pages/Documents";

const pages = [
  ["employees", "Employees", "Employee register screens will be connected in the next Phase 4 module."],
  ["attendance", "Attendance", "Attendance register screens will be connected in the next Phase 4 module."],
  ["visitors", "Visitors", "Visitor register screens will be connected in the next Phase 4 module."],
  ["suppliers", "Suppliers", "Supplier register screens will be connected in the next Phase 4 module."],
  ["spare-parts", "Spare Parts", "Inventory screens will be connected in the next Phase 4 module."],
  ["purchases", "Purchases", "Purchase screens will be connected in the next Phase 4 module."],
  ["spare-sales", "Spare Sales", "Sales screens will be connected in the next Phase 4 module."],
  ["customer-enquiries", "Customer Enquiries", "Enquiry screens will be connected in the next Phase 4 module."],
  ["documents", "Documents & OCR", "Document processing screens will be connected in the next Phase 4 module."],
  ["reports", "Reports", "Report screens will be connected in the next Phase 4 module."],
  ["users", "User Management", "User administration screens are restricted to administrators."],
];

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<PublicRoute />}>
          <Route element={<Login />} path="/login" />
          <Route element={<Navigate replace to="/login" />} path="/register" />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route element={<Dashboard />} path="/dashboard" />
            {pages.map(([path, title, description]) => (
              path === "users" ? (
                <Route element={<AdminRoute />} key={path}>
                  <Route element={<UserManagement />} path="/users" />
                </Route>
              ) : path === "employees" ? (
                <Route element={<Employees />} key={path} path={`/${path}`} />
              ) : path === "attendance" ? (
                <Route element={<Attendance />} key={path} path={`/${path}`} />
              ) : ["visitors", "suppliers", "spare-parts", "purchases", "spare-sales", "customer-enquiries"].includes(path) ? (
                <Route element={<RegisterWorkspace type={path} />} key={path} path={`/${path}`} />
              ) : path === "reports" ? (
                <Route element={<AdminRoute />} key={path}>
                  <Route element={<Reports />} path="/reports" />
                </Route>
              ) : path === "documents" ? (
                <Route element={<Documents />} key={path} path={`/${path}`} />
              ) : (
                <Route
                  element={<PlaceholderPage description={description} title={title} />}
                  key={path}
                  path={`/${path}`}
                />
              )
            ))}
          </Route>
        </Route>
        <Route element={<Navigate replace to="/dashboard" />} path="*" />
      </Routes>
    </AuthProvider>
  );
}

export default App;
