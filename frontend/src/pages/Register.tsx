import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { useAuth } from "../stores/auth";

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("analyst");
  const [error, setError] = useState("");
  const login = useAuth((s) => s.login);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/auth/register", { username, email, password, role });
      await login(username, password);
      navigate("/");
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { detail?: string } } }).response?.data;
      setError(data?.detail ?? "Erreur lors de l'inscription");
    }
  }

  return (
    <div className="mx-auto mt-20 max-w-sm rounded border bg-white p-6 shadow">
      <h1 className="mb-4 text-lg font-semibold">Créer un compte</h1>
      <form onSubmit={submit} className="space-y-3">
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Nom d'utilisateur"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={3}
        />
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Mot de passe (min. 8 caractères)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />
        <select
          className="w-full rounded border px-3 py-2"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <option value="analyst">Analyste (crée / valide / corrige)</option>
          <option value="viewer">Lecteur (consultation)</option>
        </select>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded bg-slate-900 px-3 py-2 text-white" type="submit">
          S'inscrire et se connecter
        </button>
      </form>
      <p className="mt-3 text-center text-sm text-slate-500">
        Déjà un compte ?{" "}
        <Link to="/login" className="text-slate-800 hover:underline">
          Se connecter
        </Link>
      </p>
    </div>
  );
}