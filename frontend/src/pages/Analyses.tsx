import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../lib/api";
import type { Analysis } from "../types";

export default function Analyses() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [name, setName] = useState("");
  const [ecosysteme, setEcosysteme] = useState("");
  const [flux, setFlux] = useState("");
  const [contexte, setContexte] = useState("");

  async function load() {
    const { data } = await api.get<Analysis[]>("/analyses");
    setAnalyses(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/analyses", {
      name,
      si_description: { nom: name, ecosysteme, flux, contexte_metier: contexte },
    });
    setName("");
    setEcosysteme("");
    setFlux("");
    setContexte("");
    load();
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold">Nouvelle étude</h2>
        <form onSubmit={create} className="space-y-3 rounded border bg-white p-4">
          <input
            className="w-full rounded border px-3 py-2"
            placeholder="Nom de l'étude"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <textarea
            className="w-full rounded border px-3 py-2"
            placeholder="Écosystème (serveurs, services, acteurs)"
            value={ecosysteme}
            onChange={(e) => setEcosysteme(e.target.value)}
          />
          <textarea
            className="w-full rounded border px-3 py-2"
            placeholder="Flux de données"
            value={flux}
            onChange={(e) => setFlux(e.target.value)}
          />
          <textarea
            className="w-full rounded border px-3 py-2"
            placeholder="Contexte métier"
            value={contexte}
            onChange={(e) => setContexte(e.target.value)}
          />
          <button className="rounded bg-slate-900 px-3 py-2 text-white" type="submit">
            Créer l'étude
          </button>
        </form>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold">Mes études</h2>
        <ul className="space-y-2">
          {analyses.map((a) => (
            <li key={a.id}>
              <Link
                to={`/analyses/${a.id}`}
                className="flex items-center justify-between rounded border bg-white px-4 py-3 hover:bg-slate-50"
              >
                <span>{a.name}</span>
                <span className="text-xs text-slate-500">
                  {a.status} · atelier {a.current_workshop}/5
                </span>
              </Link>
            </li>
          ))}
          {analyses.length === 0 && <p className="text-slate-500">Aucune étude pour l'instant.</p>}
        </ul>
      </div>
    </div>
  );
}
