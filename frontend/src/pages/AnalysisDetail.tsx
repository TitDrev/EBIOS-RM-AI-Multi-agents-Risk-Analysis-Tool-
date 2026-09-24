import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../lib/api";
import type {
  Analysis,
  CadrageOutput,
  ScenarioOperationnel,
  ScenarioStrategique,
  SourceRisque,
  TraitementOutput,
  Workshop,
} from "../types";

export default function AnalysisDetail() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);

  async function load() {
    const [a, w] = await Promise.all([
      api.get<Analysis>(`/analyses/${id}`),
      api.get<Workshop[]>(`/analyses/${id}/workshops`),
    ]);
    setAnalysis(a.data);
    setWorkshops(w.data);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Suivi temps réel via WebSocket → rechargement à chaque événement.
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/analyses/${id}?token=${token}`);
    ws.onmessage = () => load();
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function start() {
    setActionError(null);
    try {
      await api.post(`/analyses/${id}/start`);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: unknown } } };
      const detail = e.response?.data?.detail;
      console.error("Echec du démarrage :", err);
      setActionError(typeof detail === "string" ? detail : `Démarrage échoué${detail ? ` : ${JSON.stringify(detail)}` : ""}`);
    } finally {
      await load();
    }
  }

  async function validate(numero: number) {
    setActionError(null);
    try {
      await api.post(`/analyses/${id}/workshops/${numero}/validate`, { corrections: [] });
    } catch (err) {
      const e = err as { response?: { data?: { detail?: unknown } } };
      const detail = e.response?.data?.detail;
      console.error("Echec de la validation :", err);
      setActionError(typeof detail === "string" ? detail : `Validation échouée${detail ? ` : ${JSON.stringify(detail)}` : ""}`);
    } finally {
      await load();
    }
  }

  async function downloadReport(format: "csv" | "json" | "pdf") {
    const resp = await api.post(`/analyses/${id}/report?format=${format}`, undefined, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(resp.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `compte_rendu.${format === "json" ? "json" : format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!analysis) return <p>Chargement…</p>;

  const completed = analysis.status === "completed";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{analysis.name}</h2>
        <div className="flex gap-2">
          {analysis.status === "in_progress" || analysis.status === "awaiting_validation" ? (
            <span className="flex items-center gap-1 text-sm text-slate-500">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-green-500" />
              en direct
            </span>
          ) : null}
          {analysis.current_workshop === 0 && (
            <button className="rounded bg-slate-900 px-3 py-2 text-white" onClick={start}>
              Démarrer l'analyse
            </button>
          )}
          {completed && (
            <>
              <button
                className="rounded bg-slate-100 px-3 py-2 text-sm"
                onClick={() => downloadReport("json")}
              >
                Compte rendu JSON
              </button>
              <button
                className="rounded bg-slate-100 px-3 py-2 text-sm"
                onClick={() => downloadReport("csv")}
              >
                Registre CSV
              </button>
              <button
                className="rounded bg-slate-100 px-3 py-2 text-sm"
                onClick={() => downloadReport("pdf")}
              >
                PDF
              </button>
            </>
          )}
        </div>
      </div>

      {actionError && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </p>
      )}

      {workshops.length === 0 && <p className="text-slate-500">Aucun atelier lancé.</p>}

      {workshops.map((w) => (
        <WorkshopCard key={w.numero} workshop={w} onValidate={() => validate(w.numero)} />
      ))}
    </div>
  );
}

function WorkshopCard({ workshop, onValidate }: { workshop: Workshop; onValidate: () => void }) {
  const awaiting = workshop.status === "awaiting_validation";

  return (
    <div className="rounded border bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold">Atelier {workshop.numero}</h3>
        <span className="text-xs uppercase text-slate-500">{workshop.status}</span>
      </div>

      {workshop.numero === 1 && <Cadrage output={workshop.output as CadrageOutput} />}
      {workshop.numero === 2 && <SourcesRisques sources={(workshop.output as { sources_risques?: SourceRisque[] }).sources_risques ?? []} />}
      {workshop.numero === 3 && <Scenarios scenarios={(workshop.output as { scenarios_strategiques?: ScenarioStrategique[] }).scenarios_strategiques ?? []} />}
      {workshop.numero === 4 && <ScenariosOperationnels scenarios={(workshop.output as { scenarios_operationnels?: ScenarioOperationnel[] }).scenarios_operationnels ?? []} />}
      {workshop.numero === 5 && <Traitement output={workshop.output as TraitementOutput} />}

      {awaiting && (
        <button className="mt-3 rounded bg-green-700 px-3 py-2 text-white" onClick={onValidate}>
          Valider cet atelier
        </button>
      )}
    </div>
  );
}

function Cadrage({ output }: { output: CadrageOutput }) {
  return (
    <div className="space-y-3 text-sm">
      <div>
        <p className="font-medium">Périmètre</p>
        <p className="text-slate-600">{output.perimetre}</p>
      </div>
      <div>
        <p className="font-medium">Biens essentiels</p>
        <ul className="list-disc pl-5 text-slate-600">
          {output.biens_essentiels.map((b) => (
            <li key={b.name}>{b.name}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="font-medium">Événements redoutés</p>
        <ul className="list-disc pl-5 text-slate-600">
          {output.evenements_redoutes.map((e, i) => (
            <li key={i}>
              {e.bien_essentiel} — {e.besoin} ({e.gravite})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function SourcesRisques({ sources }: { sources: SourceRisque[] }) {
  return (
    <div className="space-y-2 text-sm">
      {sources.map((s, i) => (
        <div key={i} className="rounded border px-3 py-2">
          <span className="font-medium">{s.name}</span>
          <span className="ml-2 rounded bg-slate-100 px-2 text-xs">{s.type}</span>
          <span className="ml-2 text-xs text-slate-500">
            capacité: {s.capacite} · {s.pertinence}
          </span>
        </div>
      ))}
    </div>
  );
}

function Scenarios({ scenarios }: { scenarios: ScenarioStrategique[] }) {
  return (
    <div className="overflow-x-auto text-sm">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-1 pr-2">ID</th>
            <th className="py-1 pr-2">Source</th>
            <th className="py-1 pr-2">Événement redouté</th>
            <th className="py-1 pr-2">Gravité</th>
            <th className="py-1 pr-2">Vraisemblance</th>
            <th className="py-1">Niveau</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr key={s.identifiant} className="border-b">
              <td className="py-1 pr-2">{s.identifiant}</td>
              <td className="py-1 pr-2">{s.source_risque}</td>
              <td className="py-1 pr-2">{s.evenement_redoute}</td>
              <td className="py-1 pr-2">{s.gravite}</td>
              <td className="py-1 pr-2">{s.vraisemblance}</td>
              <td className="py-1 font-semibold">{s.niveau}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScenariosOperationnels({ scenarios }: { scenarios: ScenarioOperationnel[] }) {
  return (
    <div className="space-y-3 text-sm">
      {scenarios.map((s) => (
        <div key={s.identifiant} className="rounded border px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium">
              {s.identifiant} ({s.scenario_strategique})
            </span>
            <span className="ml-auto">G={s.gravite} V={s.vraisemblance} N={s.niveau}</span>
          </div>
          {s.techniques_attaque.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {s.techniques_attaque.map((t) => (
                <span key={t} className="rounded bg-slate-100 px-1.5 text-xs">
                  {t}
                </span>
              ))}
            </div>
          )}
          <ol className="mt-2 list-decimal pl-5 text-slate-600">
            {s.chemin_attaque.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
}

function Traitement({ output }: { output: TraitementOutput }) {
  const risques = output.risques ?? [];
  return (
    <div className="space-y-3 text-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b text-left">
              <th className="py-1 pr-2">ID</th>
              <th className="py-1 pr-2">Niveau</th>
              <th className="py-1 pr-2">Traitement</th>
              <th className="py-1 pr-2">Risque résiduel</th>
              <th className="py-1">Mesures</th>
            </tr>
          </thead>
          <tbody>
            {risques.map((r) => (
              <tr key={r.identifiant} className="border-b align-top">
                <td className="py-1 pr-2">{r.identifiant}</td>
                <td className="py-1 pr-2">{r.niveau}</td>
                <td className="py-1 pr-2">{r.traitement}</td>
                <td className="py-1 pr-2">{r.risque_residuel}</td>
                <td className="py-1">
                  <ul className="list-disc pl-4">
                    {r.mesures.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {output.plan_traitement && (
        <div>
          <p className="font-medium">Plan de traitement</p>
          <p className="text-slate-600">{output.plan_traitement}</p>
        </div>
      )}
    </div>
  );
}
