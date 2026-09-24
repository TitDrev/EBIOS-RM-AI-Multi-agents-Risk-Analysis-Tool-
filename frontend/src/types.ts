export interface Analysis {
  id: string;
  name: string;
  si_description: Record<string, string>;
  status: string;
  current_workshop: number;
}

export interface Workshop {
  id: string;
  analysis_id: string;
  numero: number;
  status: string;
  output: Record<string, unknown>;
  validated_by?: string | null;
}

export interface CadrageOutput {
  perimetre: string;
  biens_essentiels: { name: string; description: string }[];
  biens_supports: { name: string; description: string; supports: string }[];
  evenements_redoutes: {
    bien_essentiel: string;
    besoin: string;
    label: string;
    gravite: string;
  }[];
  socle_securite: { mesure: string; referentiel: string }[];
}

export interface SourceRisque {
  type: string;
  name: string;
  objectif?: string;
  motivation?: string;
  capacite?: string;
  biens_vises: string[];
  pertinence: string;
}

export interface ScenarioStrategique {
  identifiant: string;
  source_risque: string;
  evenement_redoute: string;
  bien_essentiel: string;
  gravite: string;
  vraisemblance: string;
  niveau: string;
}

export interface ScenarioOperationnel {
  identifiant: string;
  scenario_strategique: string;
  source_risque?: string;
  evenement_redoute?: string;
  chemin_attaque: string[];
  biens_supports_impliques: string[];
  techniques_attaque: string[];
  gravite: string;
  vraisemblance: string;
  niveau: string;
}
