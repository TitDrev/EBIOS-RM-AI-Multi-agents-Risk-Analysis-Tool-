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

const STATUS_CHIP: Record<string, string> = {
  pending: "bg-slate-200 text-slate-600",
  awaiting_validation: "bg-amber-400 text-amber-950",
  validated: "bg-green-500 text-white",
  failed: "bg-red-500 text-white",
  running: "bg-blue-500 text-white",
};
const STATUS_LABEL: Record<string, string> = {
  pending: "à venir",
  awaiting_validation: "à valider",
  validated: "validé",
  failed: "échec",
  running: "en cours",
};

function Badge({ value, map }: { value: string; map: Record<string, string> }) {
  const cls = map[value] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-block whitespace-nowrap rounded-md px-2 py-1 text-xs font-semibold tracking-wide ${cls}`}>
      {value}
    </span>
  );
}

function StatusChip({ status }: { status: string }) {
  const cls = STATUS_CHIP[status] ?? "bg-slate-200 text-slate-600";
  return (
    <span className={`inline-block whitespace-nowrap rounded-md px-2 py-1 text-xs font-semibold ${cls}`}>
      {STATUS_LABEL[status] ?? status}
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
      <div className="grid grid-cols-5 gap-2 sm:gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={`rounded-lg px-2 py-2 text-center shadow-sm transition ${navClass(i)} ${
              selected === i ? "ring-2 ring-slate-800 ring-offset-1" : "opacity-90"
            }`}
          >
            <span className="block text-base font-bold leading-none">Atelier {i}</span>
            <span className="mt-1 block truncate text-[10px] font-medium sm:text-[11px]">
              {WORKSHOP_LABELS[i - 1]}
            </span>
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
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        <StatusChip status={workshop.status} />
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
        <button className="mt-4 rounded-lg bg-green-700 px-4 py-2 font-medium text-white shadow-sm transition hover:bg-green-800" onClick={onValidate}>
          Valider cet atelier
        </button>
      )}
    </div>
  );
}

const TH = "border border-slate-200 bg-slate-100 px-3 py-2 text-left align-middle text-xs font-semibold uppercase tracking-wide text-slate-600";
const TD = "border border-slate-200 px-3 py-2 align-middle text-slate-700";
const TABLE = "w-full border-collapse text-sm";

function Cadrage({ output }: { output: CadrageOutput }) {
  const besoins: Record<string, string> = {
    disponibilite: "bg-blue-100 text-blue-700",
    integrite: "bg-teal-100 text-teal-700",
    confidentialite: "bg-indigo-100 text-indigo-700",
    tracabilite: "bg-fuchsia-100 text-fuchsia-700",
  };
  return (
    <div className="space-y-4 text-sm">
      <div className="rounded-lg border border-slate-200 p-3">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Périmètre</p>
        <p className="text-slate-600">{output.perimetre}</p>
      </div>

      {output.biens_essentiels.length > 0 && (
        <div className="rounded-lg border border-slate-200">
          <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Biens essentiels
          </p>
          <table className={TABLE}>
            <thead>
              <tr className="bg-slate-50/50">
                <th className={TH}>Nom</th>
                <th className={TH}>Description</th>
              </tr>
            </thead>
            <tbody>
              {output.biens_essentiels.map((b) => (
                <tr key={b.name}>
                  <td className={TD + " font-medium"}>{b.name}</td>
                  <td className={TD}>{b.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {output.biens_supports.length > 0 && (
        <div className="rounded-lg border border-slate-200">
          <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Biens supports
          </p>
          <table className={TABLE}>
            <thead>
              <tr className="bg-slate-50/50">
                <th className={TH}>Nom</th>
                <th className={TH}>Description</th>
                <th className={TH}>Supporte</th>
              </tr>
            </thead>
            <tbody>
              {output.biens_supports.map((b) => (
                <tr key={b.name}>
                  <td className={TD + " font-medium"}>{b.name}</td>
                  <td className={TD}>{b.description}</td>
                  <td className={TD}>{b.supports}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {output.evenements_redoutes.length > 0 && (
        <div className="rounded-lg border border-slate-200">
          <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Événements redoutés
          </p>
          <table className={TABLE}>
            <thead>
              <tr className="bg-slate-50/50">
                <th className={TH}>Bien</th>
                <th className={TH}>Besoin</th>
                <th className={TH}>Description</th>
                <th className={TH}>Gravité</th>
              </tr>
            </thead>
            <tbody>
              {output.evenements_redoutes.map((e, i) => (
                <tr key={i}>
                  <td className={TD}>{e.bien_essentiel}</td>
                  <td className={TD}>
                    <Badge value={e.besoin} map={besoins} />
                  </td>
                  <td className={TD}>{e.label}</td>
                  <td className={TD}>
                    <Badge value={e.gravite} map={GRAVITY} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {output.socle_securite.length > 0 && (
        <div className="rounded-lg border border-slate-200">
          <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Socle de sécurité
          </p>
          <table className={TABLE}>
            <thead>
              <tr className="bg-slate-50/50">
                <th className={TH}>Mesure</th>
                <th className={TH}>Référentiel</th>
                <th className={TH}>Écart</th>
              </tr>
            </thead>
            <tbody>
              {output.socle_securite.map((m, i) => (
                <tr key={i}>
                  <td className={TD}>{m.mesure}</td>
                  <td className={TD}>{m.referentiel}</td>
                  <td className={TD}>{m.ecart || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
    <div className="rounded-lg border border-slate-200">
      <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Sources de risques (SR / objectif visé)
      </p>
      <div className="overflow-x-auto">
        <table className={TABLE}>
        <thead>
          <tr className="bg-slate-50/50">
            <th className={TH}>Type</th>
            <th className={TH}>Nom</th>
            <th className={TH}>Objectif (OV)</th>
            <th className={TH}>Motivation</th>
            <th className={TH}>Capacité</th>
            <th className={TH}>Biens visés</th>
            <th className={TH}>Pertinence</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s, i) => (
            <tr key={i}>
              <td className={TD}>
                <Badge value={s.type} map={SOURCE_TYPE} />
              </td>
              <td className={TD + " font-medium"}>{s.name}</td>
              <td className={TD}>{s.objectif}</td>
              <td className={TD}>{s.motivation}</td>
              <td className={TD}>
                {s.capacite ? <Badge value={s.capacite} map={GRAVITY} /> : "—"}
              </td>
              <td className={TD}>{s.biens_vises.join(", ")}</td>
              <td className={TD}>
                <Badge value={s.pertinence} map={pertinence} />
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  );
}

function Scenarios({ scenarios }: { scenarios: ScenarioStrategique[] }) {
  if (scenarios.length === 0) return <p className="text-sm text-slate-500">Aucun scénario.</p>;
  return (
    <div className="rounded-lg border border-slate-200">
      <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Scénarios stratégiques
      </p>
      <div className="overflow-x-auto">
        <table className={TABLE}>
          <thead>
            <tr className="bg-slate-50/50">
              <th className={TH}>ID</th>
              <th className={TH}>Source</th>
              <th className={TH}>Événement redouté</th>
              <th className={TH}>Bien</th>
              <th className={TH}>Gravité</th>
              <th className={TH}>Vraisemblance</th>
              <th className={TH}>Niveau</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s) => (
              <tr key={s.identifiant}>
                <td className={TD + " font-semibold"}>{s.identifiant}</td>
                <td className={TD}>{s.source_risque}</td>
                <td className={TD}>{s.evenement_redoute}</td>
                <td className={TD}>{s.bien_essentiel}</td>
                <td className={TD}>
                  <Badge value={s.gravite} map={GRAVITY} />
                </td>
                <td className={TD}>
                  <Badge value={s.vraisemblance} map={LIKELIHOOD} />
                </td>
                <td className={TD}>
                  <Badge value={s.niveau} map={LEVEL} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScenariosOperationnels({ scenarios }: { scenarios: ScenarioOperationnel[] }) {
  if (scenarios.length === 0) return <p className="text-sm text-slate-500">Aucun scénario.</p>;
  return (
    <div className="rounded-lg border border-slate-200">
      <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Scénarios opérationnels
      </p>
      <div className="overflow-x-auto">
        <table className={TABLE}>
          <thead>
            <tr className="bg-slate-50/50">
              <th className={TH}>ID</th>
              <th className={TH}>Stratégique</th>
              <th className={TH}>Source</th>
              <th className={TH}>Événement</th>
              <th className={TH}>Gravité</th>
              <th className={TH}>Vraisemblance</th>
              <th className={TH}>Niveau</th>
              <th className={TH}>Techniques</th>
              <th className={TH}>Chemin d'attaque</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s) => (
              <tr key={s.identifiant}>
                <td className={TD + " font-semibold"}>{s.identifiant}</td>
                <td className={TD}>{s.scenario_strategique}</td>
                <td className={TD}>{s.source_risque}</td>
                <td className={TD}>{s.evenement_redoute}</td>
                <td className={TD}>
                  <Badge value={s.gravite} map={GRAVITY} />
                </td>
                <td className={TD}>
                  <Badge value={s.vraisemblance} map={LIKELIHOOD} />
                </td>
                <td className={TD}>
                  <Badge value={s.niveau} map={LEVEL} />
                </td>
                <td className={TD}>
                  <div className="flex flex-wrap gap-1">
                    {s.techniques_attaque.map((t) => (
                      <span key={t} className="rounded bg-slate-100 px-1.5 text-xs">
                        {t}
                      </span>
                    ))}
                  </div>
                </td>
                <td className={TD}>
                  <ol className="list-decimal pl-4 text-slate-600">
                    {s.chemin_attaque.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Traitement({ output }: { output: TraitementOutput }) {
  const risques = output.risques ?? [];
  return (
    <div className="space-y-4 text-sm">
      <div className="rounded-lg border border-slate-200">
        <p className="border-b bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Registre des risques
        </p>
        <div className="overflow-x-auto">
          <table className={TABLE}>
            <thead>
              <tr className="bg-slate-50/50">
                <th className={TH}>ID</th>
                <th className={TH}>Événement</th>
                <th className={TH}>Gravité</th>
                <th className={TH}>Vraisemblance</th>
                <th className={TH}>Niveau</th>
                <th className={TH}>Traitement</th>
                <th className={TH}>Résiduel</th>
                <th className={TH}>Mesures</th>
              </tr>
            </thead>
            <tbody>
              {risques.map((r) => (
                <tr key={r.identifiant}>
                  <td className={TD + " font-semibold"}>{r.identifiant}</td>
                  <td className={TD}>{r.evenement_redoute || r.scenario_operationnel}</td>
                  <td className={TD}>
                    <Badge value={r.gravite} map={GRAVITY} />
                  </td>
                  <td className={TD}>
                    <Badge value={r.vraisemblance} map={LIKELIHOOD} />
                  </td>
                  <td className={TD}>
                    <Badge value={r.niveau} map={LEVEL} />
                  </td>
                  <td className={TD}>
                    <span className={TREATMENT[r.traitement] ?? ""}>{r.traitement}</span>
                  </td>
                  <td className={TD}>
                    <Badge value={r.risque_residuel} map={LEVEL} />
                  </td>
                  <td className={TD}>
                    <ul className="list-disc pl-4 text-slate-600">
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
      </div>
      {output.plan_traitement && (
        <div className="rounded border p-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Plan de traitement
          </p>
          <p className="text-slate-600">{output.plan_traitement}</p>
        </div>
      )}
    </div>
  );
}