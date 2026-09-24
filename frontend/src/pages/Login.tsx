import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../stores/auth";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const login = useAuth((s) => s.login);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Identifiants invalides");
    }
  }

  return (
    <div className="mx-auto mt-20 max-w-sm rounded border bg-white p-6 shadow">
      <h1 className="mb-4 text-lg font-semibold">Connexion</h1>
      <form onSubmit={submit} className="space-y-3">
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Nom d'utilisateur"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Mot de passe"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded bg-slate-900 px-3 py-2 text-white" type="submit">
          Se connecter
        </button>
      </form>
    </div>
  );
}
