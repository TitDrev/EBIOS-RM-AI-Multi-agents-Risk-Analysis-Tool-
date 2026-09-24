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

const WORKSHOP_LABELS = [
  "Cadrage & socle",
  "Sources de risques",
  "Scénarios stratégiques",
  "Scénarios opérationnels",
  "Traitement du risque",
];

const GRAVITY: Record<string, string> = {
  g1: "bg-emerald-100 text-emerald-700",
  g2: "bg-lime-100 text-lime-800",
  g3: "bg-amber-100 text-amber-800",
  g4: "bg-red-100 text-red-700",
};
const LIKELIHOOD: Record<string, string> = {
  v1: "bg-slate-100 text-slate-600",
  v2: "bg-sky-100 text-sky-700",
  v3: "bg-indigo-100 text-indigo-700",
  v4: "bg-purple-100 text-purple-700",
};
const LEVEL: Record<string, string> = {
  faible: "bg-emerald-100 text-emerald-700",
  moyen: "bg-yellow-100 text-yellow-800",
  eleve: "bg-orange-100 text-orange-800",
  critique: "bg-red-100 text-red-700",
};
const SOURCE_TYPE: Record<string, string> = {
  attaquant_externe: "bg-red-100 text-red-700",
  interne_malveillant: "bg-orange-100 text-orange-800",
  interne_negligent: "bg-yellow-100 text-yellow-800",
  sinistre_naturel: "bg-sky-100 text-sky-700",
  sinistre_accidentel: "bg-slate-100 text-slate-600",
  autre: "bg-slate-100 text-slate-600",
};
const TREATMENT: Record<string, string> = {
  reduire: "text-blue-700 font-semibold",
  transferer: "text-purple-700 font-semibold",
  eviter: "text-slate-500 font-semibold",
  accepter: "text-amber-700 font-semibold",
};

function Badge({ value, map }: { value: string; map: Record<string, string> }) {
  const cls = map[value] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-block whitespace-nowrap rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>
      {value}
    </span>
  );
}

export default function AnalysisDetail() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [selected, setSelected] = useState(1);
  const [running, setRunning] = useState<{ numero: number } | null>(null);
  const [progress, setProgress] = useState<{ pct: number; phase: string } | null>(null);
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

  useEffect(() => {
    if (analysis && analysis.current_workshop > 0 && analysis.current_workshop <= 5) {
      setSelected(analysis.current_workshop);
    }
  }, [analysis?.current_workshop]); // eslint-disable-line react-hooks/exhaustive-deps

  // Suivi temps réel (progression + événements d'atelier)
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/analyses/${id}?token=${token}`);
    ws.onmessage = (ev) => {
      let msg: unknown = null;
      try {
        msg = JSON.parse(ev.data as string);
      } catch {
        load();
        return;
      }
      const m = msg as { type?: string; numero?: number; pct?: number; phase?: string };
      if (m.type === "workshop_running" && m.numero) {
        setRunning({ numero: m.numero });
        setSelected(m.numero);
        setProgress({ pct: 5, phase: "préparation" });
      } else if (m.type === "workshop_progress") {
        setProgress({ pct: m.pct ?? 0, phase: m.phase ?? "en cours…" });
      } else {
        setRunning(null);
        setProgress(null);
        load();
      }
    };
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

  async function downloadReport(format: "json" | "csv" | "pdf" | "xlsx") {
    const resp = await api.post(`/analyses/${id}/report?format=${format}`, undefined, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(resp.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `compte_rendu.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!analysis) return <p>Chargement…</p>;

  const completed = analysis.status === "completed";
  const wsMap = Object.fromEntries(workshops.map((w) => [w.numero, w]));

  function navClass(i: number): string {
    if (running?.numero === i) return "bg-blue-500 text-white animate-pulse";
    const w = wsMap[i];
    if (!w) return "bg-slate-200 text-slate-500";
    switch (w.status) {
      case "validated":
        return "bg-green-500 text-white";
      case "awaiting_validation":
        return "bg-amber-400 text-white";
      case "failed":
        return "bg-red-500 text-white";
      default:
        return "bg-slate-200 text-slate-500";
    }
  }

  const activeWs = wsMap[selected];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">{analysis.name}</h2>
        <div className="flex flex-wrap gap-2">
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
              <button className="rounded bg-slate-100 px-3 py-2 text-sm" onClick={() => downloadReport("json")}>
                JSON
              </button>
              <button className="rounded bg-slate-100 px-3 py-2 text-sm" onClick={() => downloadReport("csv")}>
                CSV
              </button>
              <button className="rounded bg-slate-100 px-3 py-2 text-sm" onClick={() => downloadReport("pdf")}>
                PDF
              </button>
              <button className="rounded bg-green-100 px-3 py-2 text-sm font-medium text-green-800" onClick={() => downloadReport("xlsx")}>
                Excel
              </button>
            </>
          )}
        </div>
      </div>

      {/* Barre de navigation des 5 ateliers */}
      <div className="grid grid-cols-5 gap-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={`rounded px-2 py-2 text-center transition ${navClass(i)} ${
              selected === i ? "ring-2 ring-slate-700" : ""
            }`}
          >
            <span className="block text-sm font-semibold">{i}</span>
            <span className="block truncate text-[10px]">{WORKSHOP_LABELS[i - 1]}</span>
          </button>
        ))}
      </div>

      {/* Indicateur de progression de l'atelier en cours */}
      {running && (
        <div className="rounded border bg-white p-3">
          <div className="h-2 w-full overflow-hidden rounded bg-slate-200">
            <div
              className="h-2 rounded bg-blue-500 transition-all"
              style={{ width: `${Math.min(progress?.pct ?? 5, 100)}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Atelier {running.numero} {WORKSHOP_LABELS[running.numero - 1]} ·{" "}
            {progress?.phase ?? "en cours…"} ({progress?.pct ?? 0} %)
          </p>
        </div>
      )}

      {actionError && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </p>
      )}

      {/* Atelier sélectionné */}
      {!activeWs ? (
        <p className="rounded border border-dashed bg-white p-4 text-sm text-slate-500">
          {running?.numero === selected
            ? `Atelier ${selected} en cours de réalisation…`
            : `Atelier ${selected} non réalisé pour l'instant.`}
        </p>
      ) : (
        <WorkshopCard workshop={activeWs} onValidate={() => validate(activeWs.numero)} />
      )}
    </div>
  );
}

function WorkshopCard({ workshop, onValidate }: { workshop: Workshop; onValidate: () => void }) {
  const awaiting = workshop.status === "awaiting_validation";
  const title = `Atelier ${workshop.numero} — ${WORKSHOP_LABELS[workshop.numero - 1]}`;

  return (
    <div className="rounded border bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold">{title}</h3>
        <span className="text-xs uppercase text-slate-500">{workshop.status}</span>
      </div>

      {workshop.numero === 1 && <Cadrage output={workshop.output as CadrageOutput} />}
      {workshop.numero === 2 && (
        <SourcesRisques sources={(workshop.output as { sources_risques?: SourceRisque[] }).sources_risques ?? []} />
      )}
      {workshop.numero === 3 && (
        <Scenarios
          scenarios={(workshop.output as { scenarios_strategiques?: ScenarioStrategique[] }).scenarios_strategiques ?? []}
        />
      )}
      {workshop.numero === 4 && (
        <ScenariosOperationnels
          scenarios={(workshop.output as { scenarios_operationnels?: ScenarioOperationnel[] }).scenarios_operationnels ?? []}
        />
      )}
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
  const besoins: Record<string, string> = {
    disponibilite: "bg-blue-100 text-blue-700",
    integrite: "bg-teal-100 text-teal-700",
    confidentialite: "bg-indigo-100 text-indigo-700",
    tracabilite: "bg-fuchsia-100 text-fuchsia-700",
  };
  return (
    <div className="space-y-3 text-sm">
      <div>
        <p className="font-medium text-slate-700">Périmètre</p>
        <p className="text-slate-600">{output.perimetre}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <p className="font-medium text-slate-700">Biens essentiels</p>
          <ul className="mt-1 space-y-1 text-slate-600">
            {output.biens_essentiels.map((b) => (
              <li key={b.name} className="rounded bg-slate-50 px-2 py-1">
                {b.name}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-medium text-slate-700">Biens supports</p>
          <ul className="mt-1 space-y-1 text-slate-600">
            {output.biens_supports.map((b) => (
              <li key={b.name} className="rounded bg-slate-50 px-2 py-1">
                {b.name} <span className="text-xs text-slate-400">→ {b.supports}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div>
        <p className="font-medium text-slate-700">Événements redoutés</p>
        <div className="mt-1 space-y-1">
          {output.evenements_redoutes.map((e, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2 rounded bg-slate-50 px-2 py-1">
              <span className="text-slate-600">{e.label}</span>
              <Badge value={e.besoin} map={besoins} />
              <Badge value={e.gravite} map={GRAVITY} />
            </div>
          ))}
        </div>
      </div>
      {output.socle_securite.length > 0 && (
        <div>
          <p className="font-medium text-slate-700">Socle de sécurité</p>
          <ul className="mt-1 space-y-1 text-slate-600">
            {output.socle_securite.map((m, i) => (
              <li key={i} className="rounded bg-slate-50 px-2 py-1">
                {m.mesure} <span className="text-xs text-slate-400">· {m.referentiel}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function SourcesRisques({ sources }: { sources: SourceRisque[] }) {
  const pertinence: Record<string, string> = {
    retenue: "bg-green-100 text-green-700",
    ecartee: "bg-slate-100 text-slate-500",
    a_suivre: "bg-amber-100 text-amber-700",
  };
  if (sources.length === 0) return <p className="text-sm text-slate-500">Aucune source.</p>;
  return (
    <div className="space-y-2 text-sm">
      {sources.map((s, i) => (
        <div key={i} className="rounded border px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium">{s.name}</span>
            <Badge value={s.type} map={SOURCE_TYPE} />
            <Badge value={s.pertinence} map={pertinence} />
            {s.capacite && (
              <span className="ml-auto text-xs text-slate-500">
                capacité <Badge value={s.capacite} map={GRAVITY} />
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {s.objectif} · {s.motivation}
            {s.biens_vises.length > 0 && ` · vise : ${s.biens_vises.join(", ")}`}
          </p>
        </div>
      ))}
    </div>
  );
}

function Scenarios({ scenarios }: { scenarios: ScenarioStrategique[] }) {
  if (scenarios.length === 0) return <p className="text-sm text-slate-500">Aucun scénario.</p>;
  return (
    <div className="overflow-x-auto text-sm">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-1 pr-2">ID</th>
            <th className="py-1 pr-2">Source</th>
            <th className="py-1 pr-2">Événement redouté</th>
            <th className="py-1 pr-2">Bien</th>
            <th className="py-1 pr-2">Gravité</th>
            <th className="py-1 pr-2">Vraisemblance</th>
            <th className="py-1">Niveau</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr key={s.identifiant} className="border-b align-top">
              <td className="py-1 pr-2 font-semibold">{s.identifiant}</td>
              <td className="py-1 pr-2">{s.source_risque}</td>
              <td className="py-1 pr-2">{s.evenement_redoute}</td>
              <td className="py-1 pr-2">{s.bien_essentiel}</td>
              <td className="py-1 pr-2">
                <Badge value={s.gravite} map={GRAVITY} />
              </td>
              <td className="py-1 pr-2">
                <Badge value={s.vraisemblance} map={LIKELIHOOD} />
              </td>
              <td className="py-1">
                <Badge value={s.niveau} map={LEVEL} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScenariosOperationnels({ scenarios }: { scenarios: ScenarioOperationnel[] }) {
  if (scenarios.length === 0) return <p className="text-sm text-slate-500">Aucun scénario.</p>;
  return (
    <div className="space-y-3 text-sm">
      {scenarios.map((s) => (
        <div key={s.identifiant} className="rounded border px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">
              {s.identifiant} ({s.scenario_strategique})
            </span>
            <Badge value={s.gravite} map={GRAVITY} />
            <Badge value={s.vraisemblance} map={LIKELIHOOD} />
            <Badge value={s.niveau} map={LEVEL} />
            <span className="ml-auto text-xs text-slate-500">{s.source_risque}</span>
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
              <th className="py-1 pr-2">Événement</th>
              <th className="py-1 pr-2">Gravité</th>
              <th className="py-1 pr-2">Vraisemblance</th>
              <th className="py-1 pr-2">Niveau</th>
              <th className="py-1 pr-2">Traitement</th>
              <th className="py-1">Résiduel</th>
            </tr>
          </thead>
          <tbody>
            {risques.map((r) => (
              <tr key={r.identifiant} className="border-b align-top">
                <td className="py-1 pr-2 font-semibold">{r.identifiant}</td>
                <td className="py-1 pr-2">{r.evenement_redoute || r.scenario_operationnel}</td>
                <td className="py-1 pr-2">
                  <Badge value={r.gravite} map={GRAVITY} />
                </td>
                <td className="py-1 pr-2">
                  <Badge value={r.vraisemblance} map={LIKELIHOOD} />
                </td>
                <td className="py-1 pr-2">
                  <Badge value={r.niveau} map={LEVEL} />
                </td>
                <td className="py-1 pr-2">
                  <span className={TREATMENT[r.traitement] ?? ""}>{r.traitement}</span>
                </td>
                <td className="py-1">
                  <Badge value={r.risque_residuel} map={LEVEL} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {risques[0] && (
        <div>
          <p className="font-medium text-slate-700">Mesures proposées</p>
          <ul className="mt-1 space-y-1 text-slate-600">
            {risques[0].mesures.map((m, i) => (
              <li key={i} className="rounded bg-slate-50 px-2 py-1">
                {m}
              </li>
            ))}
          </ul>
        </div>
      )}
      {output.plan_traitement && (
        <div>
          <p className="font-medium text-slate-700">Plan de traitement</p>
          <p className="text-slate-600">{output.plan_traitement}</p>
        </div>
      )}
    </div>
  );
}