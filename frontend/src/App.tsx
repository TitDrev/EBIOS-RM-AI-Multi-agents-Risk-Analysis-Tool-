import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Analyses from "./pages/Analyses";
import AnalysisDetail from "./pages/AnalysisDetail";
import Compare from "./pages/Compare";
import { useAuth } from "./stores/auth";

export default function App() {
  const token = useAuth((s) => s.token);

  return (
    <BrowserRouter>
      <main className="min-h-screen bg-slate-50 text-slate-900">
        <header className="flex items-center justify-between border-b bg-white px-6 py-4">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">Agents IA — Analyse de risques (EBIOS RM)</h1>
            {token && (
              <nav className="flex gap-3 text-sm text-slate-500">
                <Link to="/" className="hover:text-slate-800">
                  Études
                </Link>
                <Link to="/compare" className="hover:text-slate-800">
                  Comparer
                </Link>
              </nav>
            )}
          </div>
          {token && <Logout />}
        </header>
        <section className="mx-auto max-w-5xl p-6">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={token ? <Analyses /> : <Navigate to="/login" />} />
            <Route
              path="/compare"
              element={token ? <Compare /> : <Navigate to="/login" />}
            />
            <Route
              path="/analyses/:id"
              element={token ? <AnalysisDetail /> : <Navigate to="/login" />}
            />
          </Routes>
        </section>
      </main>
    </BrowserRouter>
  );
}

function Logout() {
  const logout = useAuth((s) => s.logout);
  return (
    <button className="text-sm text-slate-500 hover:text-slate-800" onClick={logout}>
      Déconnexion
    </button>
  );
}
