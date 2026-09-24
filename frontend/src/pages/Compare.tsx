import { useEffect, useState } from "react";
import api from "../lib/api";
import type { Analysis } from "../types";

interface Snapshot {
  nom: string;
  statut: string;
  atelier_courant: number;
  biens: number;
  sources_de_risques: number;
  scenarios_strategiques: number;
  scenarios_operationnels: number;
  risques: number;
  par_niveau: Record<string, number>;
}

interface CompareResult {
  etude_a: Snapshot;
  etude_b: Snapshot;
  differences: Record<string, { a: number; b: number; delta: number }>;
}

const METRICS: Array<[string, keyof Snapshot]> = [
  ["Biens", "biens"],
  ["Sources de risques", "sources_de_risques"],
  ["Scénarios stratégiques", "scenarios_strategiques"],
  ["Scénarios opérationnels", "scenarios_operationnels"],
  ["Risques", "risques"],
];

export default function Compare() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);

  useEffect(() => {
    api.get<Analysis[]>("/analyses").then((r) => setAnalyses(r.data));
  }, []);

  async function run() {
    if (!a || !b) return;
    const { data } = await api.post<CompareResult>("/analyses/compare", {
      etude_a: a,
      etude_b: b,
    });
    setResult(data);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Comparer deux études</h2>
      <div className="grid max-w-lg grid-cols-2 gap-2">
        <select
          className="rounded border px-3 py-2"
          value={a}
          onChange={(e) => setA(e.target.value)}
        >
          <option value="">Étude A…</option>
          {analyses.map((x) => (
            <option key={x.id} value={x.id}>
              {x.name}
            </option>
          ))}
        </select>
        <select
          className="rounded border px-3 py-2"
          value={b}
          onChange={(e) => setB(e.target.value)}
        >
          <option value="">Étude B…</option>
          {analyses.map((x) => (
            <option key={x.id} value={x.id}>
              {x.name}
            </option>
          ))}
        </select>
        <button
          className="rounded bg-slate-900 px-3 py-2 text-white disabled:opacity-50"
          onClick={run}
          disabled={!a || !b}
        >
          Comparer
        </button>
      </div>

      {result && (
        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="px-3 py-2">Métrique</th>
                <th className="px-3 py-2">{result.etude_a.nom}</th>
                <th className="px-3 py-2">{result.etude_b.nom}</th>
                <th className="px-3 py-2">Écart</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map(([label, key]) => {
                const d = result.differences[key];
                return (
                  <tr key={key} className="border-b">
                    <td className="px-3 py-2">{label}</td>
                    <td className="px-3 py-2">{d.a}</td>
                    <td className="px-3 py-2">{d.b}</td>
                    <td className="px-3 py-2">{d.delta > 0 ? `+${d.delta}` : d.delta}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="px-3 py-2 text-xs text-slate-500">
            Répartition par niveau — A : {JSON.stringify(result.etude_a.par_niveau)} · B :{" "}
            {JSON.stringify(result.etude_b.par_niveau)}
          </p>
        </div>
      )}
    </div>
  );
}