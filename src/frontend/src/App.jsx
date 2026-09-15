import { Routes, Route, NavLink, Outlet, useLocation } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard,
  Plane,
  Wrench,
  SlidersHorizontal,
  Bot,
  ShieldCheck,
} from "lucide-react";
import { api } from "./services/api";
import Dashboard from "./pages/Dashboard";
import Fleet from "./pages/Fleet";
import AssetDetails from "./pages/AssetDetails";
import Maintenance from "./pages/Maintenance";
import CustomPrediction from "./pages/CustomPrediction";
import Copilot from "./pages/Copilot";

const NAV_ITEMS = [
  { path: "/",                  label: "Dashboard",         Icon: LayoutDashboard },
  { path: "/fleet",             label: "Fleet",             Icon: Plane },
  { path: "/maintenance",       label: "Maintenance",       Icon: Wrench },
  { path: "/custom-prediction", label: "Custom Prediction", Icon: SlidersHorizontal },
  { path: "/copilot",           label: "Copilot",           Icon: Bot },
];

/* Separate component so it can call useLocation for icon colour */
function NavItem({ path, label, Icon, onClose }) {
  const location = useLocation();
  const isActive = path === "/"
    ? location.pathname === "/"
    : location.pathname.startsWith(path);

  return (
    <NavLink
      to={path}
      end={path === "/"}
      className={isActive ? "active" : ""}
      onClick={onClose}
    >
      <span className="nav-icon">
        <Icon size={18} strokeWidth={2} color={isActive ? "#3B82F6" : "#6B7280"} />
      </span>
      {label}
    </NavLink>
  );
}

function Header({ onMenuClick }) {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    const check = () =>
      api.getHealth()
        .then(() => setOnline(true))
        .catch(() => setOnline(false));
    check();
    const intv = setInterval(check, 30000);
    return () => clearInterval(intv);
  }, []);

  return (
    <header className="header">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button className="hamburger" onClick={onMenuClick} aria-label="Toggle navigation">
          ☰
        </button>
        <div>
          <h1>Mission Readiness &amp; Predictive Maintenance</h1>
          <div className="subtitle">Fleet health · RUL · Anomaly detection · Maintenance prioritisation</div>
        </div>
      </div>
      <div className="status-pill">
        <span className={`status-dot ${online ? "" : "offline"}`} />
        API: {online ? "Online" : "Offline"}
      </div>
    </header>
  );
}

function Sidebar({ open, onClose }) {
  return (
    <>
      <div
        className={`sidebar-overlay ${open ? "open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="logo">
            <ShieldCheck size={20} strokeWidth={2} color="#fff" />
          </div>
          <div className="brand-text">
            <strong>Readiness Copilot</strong>
            <span>v1.0 · NASA C-MAPSS</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ path, label, Icon }) => (
            <NavItem
              key={path}
              path={path}
              label={label}
              Icon={Icon}
              onClose={onClose}
            />
          ))}
        </nav>
        <div className="sidebar-footer">
          ML: Random Forest + Isolation Forest<br />
          Data: NASA C-MAPSS FD001
        </div>
      </aside>
    </>
  );
}

function AnimatedOutlet() {
  const location = useLocation();
  return (
    <div className="page-enter" key={location.pathname}>
      <Outlet />
    </div>
  );
}

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const openSidebar  = useCallback(() => setSidebarOpen(true),  []);
  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  return (
    <div className="app">
      <div className="app-layout">
        <Sidebar open={sidebarOpen} onClose={closeSidebar} />
        <div className="main-content">
          <Header onMenuClick={openSidebar} />
          <main className="content">
            <AnimatedOutlet />
          </main>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="fleet" element={<Fleet />} />
        <Route path="assets/:assetId" element={<AssetDetails />} />
        <Route path="maintenance" element={<Maintenance />} />
        <Route path="custom-prediction" element={<CustomPrediction />} />
        <Route path="copilot" element={<Copilot />} />
      </Route>
    </Routes>
  );
}