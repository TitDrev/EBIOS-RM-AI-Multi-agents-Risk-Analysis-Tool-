# Cahier des charges v2 – Système multi-agents IA d'analyse de risques selon EBIOS Risk Manager

> Version adaptée au projet « Des agents IA pour analyser les risques » (E21 · Management de la sécurité · M2 Cybersécurité).
> La démarche d'analyse de risques est fondée sur la méthode **EBIOS Risk Manager** (ANSSI) et ses **5 ateliers**, reproduits par un système **multi-agents** avec **validation humaine entre chaque atelier** et production d'un **compte rendu** final.

---

## 1. Objectif

Développer une **application web complète, multi-agents**, permettant à un analyste de sécurité de conduire une analyse de risques conforme à la méthode **EBIOS Risk Manager** sur **n'importe quel système d'information** (SI).

Concrètement, l'utilisateur fournit la **description d'un SI** (écosystème, flux de données, contexte métier, contraintes). Un **système de plusieurs agents IA spécialisés** déroule les **5 ateliers EBIOS RM** :

1. **Cadrage et socle de sécurité**
2. **Sources de risques**
3. **Scénarios stratégiques**
4. **Scénarios opérationnels**
5. **Traitement du risque**

**Entre chaque atelier, un humain valide** (ou corrige) le résultat avant que l'atelier suivant ne démarre. À la fin, le système produit un **compte rendu** complet (registre des risques, plan de traitement, justification) soumis à validation.

Le but n'est **pas de remplacer l'analyste**, mais de **l'assister** : l'humain reste responsable de la décision finale.

### Principes directeurs

- **Générique** : les 5 ateliers s'exécutent sur *n'importe quel SI* (boutique en ligne, téléconsultation, réseau de PME, cas personnalisé…).
- **Multi-agents** : un agent spécialisé par atelier, orchestré, chacun avec une consigne courte et des outils limités.
- **Validation humaine entre ateliers** : chaque sortie d'atelier est relue et validée avant la poursuite.
- **Vérifiable** : chaque résultat est structuré (JSON), sourcé et traçable.
- **Maîtrisé** : les faiblesses de l'IA (hallucination, injection de prompt, fuite de données) sont explicitement traitées.

---

## 2. Architecture technique

### Backend

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Langage | Python 3.11+ | Écosystème IA dominant (LangChain, LangGraph, embeddings) |
| Framework API | FastAPI | Asynchrone, documentation OpenAPI/Swagger auto-générée |
| Orchestration d'agents | LangGraph (LangChain) | Graphe d'états typé, reprises ciblées, `interrupt` pour validation humaine entre ateliers |
| LLM | Couche d'abstraction `llm-provider` (modèles **Opencode Go**, ex. `deepseek-v4-pro`) | Modèle remplaçable, pas de couplage à un fournisseur |
| Base de données | PostgreSQL 16 + **pgvector** | Données relationnelles (registre, ateliers) + stockage d'embeddings (RAG) |
| File d'attente | Celery + Redis | Tâches longues (déroulé complet des 5 ateliers) |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Standard, typage, migrations |
| RAG / base de connaissances | Embeddings + pgvector | Fournit EBIOS RM, ISO 27005, ISO 27002, guides ANSSI, MITRE ATT&CK aux agents |

### Frontend

| Composant | Choix |
|-----------|-------|
| Framework | React 18 + TypeScript |
| Styling | Tailwind CSS 3 |
| State management | Zustand |
| Visualisation | Chart.js / D3.js (cartographie gravité × vraisemblance, chemin d'attaque) |
| API client | Axios |
| Temps réel | WebSocket (suivi des ateliers, demande de validation) |

### Infrastructure

| Composant | Choix |
|-----------|-------|
| Conteneurisation | Docker + Docker Compose |
| Reverse proxy | Nginx |
| CI/CD | GitHub Actions |
| Déploiement | Docker Compose (dev) / Docker Swarm ou K8s (prod) |

---

## 3. Glossaire

### EBIOS Risk Manager (vocabulaire de la méthode)

| Terme | Définition |
|-------|-----------|
| **EBIOS RM** | Méthode d'analyse de risques de l'ANSSI, structurée en 5 ateliers |
| **Bien essentiel (valeur métier)** | Ce qui a de la valeur pour l'organisation (processus métier, donnée, image…) |
| **Bien support** | Élément qui supporte un bien essentiel (serveur, application, compte, local…) |
| **Besoins de sécurité (DICP)** | Disponibilité, Intégrité, Confidentialité, Traçabilité — critères d'évaluation |
| **Événement redouté** | Conséquence négative sur un bien essentiel (indisponibilité, fuite, altération…) |
| **Source de risques (SR)** | Origine du danger : attaquant, personnel interne malveillant/négligent, sinistre naturel/accidentel |
| **Scénario stratégique** | Croisement source de risques × événement redouté, évalué en gravité et vraisemblance |
| **Scénario opérationnel** | Déroulé concret d'une attaque (chemin d'attaque, techniques) sur les biens supports |
| **Gravité** | Importance de l'impact si l'événement redouté survient |
| **Vraisemblance** | Possibilité que le scénario se réalise |
| **Socle de sécurité** | Mesures de sécurité existantes ou déjà prévues |
| **Traitement du risque** | Stratégie : réduire, transférer, éviter, accepter |
| **Risque résiduel** | Risque restant après application des mesures |
| **Plan de traitement** | Liste des mesures à mettre en œuvre et de leurs responsables |

### Intelligence artificielle

| Terme | Définition |
|-------|-----------|
| **LLM** | Grand modèle de langage (GPT, DeepSeek…) |
| **Prompt** | Consigne écrite donnée au LLM : rôle, tâche, format attendu |
| **Agent IA** | Programme qui utilise un LLM pour planifier, agir par étapes et appeler des outils |
| **Orchestrateur** | Agent « chef d'orchestre » qui enchaîne les ateliers et fait circuler les résultats |
| **RAG** | Fournir au LLM des documents de référence fiables pour réduire les hallucinations |
| **Humain dans la boucle** | Validation humaine obligatoire entre les ateliers |
| **Hallucination** | Information fausse mais crédible inventée par l'IA |
| **Injection de prompt** | Texte piégé dans une donnée qui détourne les consignes de l'agent |
| **Empoisonnement** | Base de connaissances contenant de fausses informations |

---

## 4. Choix techniques détaillés

### 4.1 Framework d'agents

| Option | Évaluée | Décision |
|--------|---------|----------|
| LangGraph | Graphe d'états, cycles, reprises, `interrupt` pour validation humaine entre ateliers | **Retenu** |
| CrewAI | Simple, orienté rôles, mais contrôle fin plus limité | Écarté |
| AutoGen | Orienté conversation, moins adapté à un pipeline déterministe | Écarté |
| Sans framework | Pur LLM + prompts : faisable mais réinvente l'orchestration | Écarté |

**Décision :** LangGraph. Chaque atelier EBIOS RM est un **nœud** du graphe, suivi d'un **point de validation humaine** (`interrupt`). Les **reprises ciblées** permettent de corriger un atelier sans refaire les précédents.

### 4.2 Fournisseur de LLM

| Source | Accès | Remarque |
|--------|-------|----------|
| **Opencode Go** | API (modèles `deepseek-v4-pro`, etc.) | **Retenu** — modèles proposés par la solution Opencode Go |

**Décision :** une couche d'abstraction `LLMProvider` (interface unique `complete(prompt, tools) → réponse structurée`) permet de brancher n'importe quel modèle Opencode Go et de **remplacer le modèle sans toucher aux agents**. Les cas analysés étant **100 % fictifs**, aucune anonymisation n'est requise (mais la couche est prête à l'ajouter).

### 4.3 Base de connaissances (RAG)

| Source | Contenu | Atelier concerné |
|--------|---------|------------------|
| EBIOS RM (ANSSI) | Méthodologie, fiches d'atelier | Tous |
| ISO/IEC 27005 | Démarche d'appréciation du risque | Atelier 5 |
| ISO/IEC 27002 | Catalogue de mesures | Ateliers 1, 5 |
| Guides ANSSI | Mesures et référentiels (hygiène informatique…) | Ateliers 1, 5 |
| MITRE ATT&CK (STIX) | Techniques d'attaque réelles | Atelier 4 |
| NVD (CVE/CVSS) | Vulnérabilités connues | Atelier 4 |

**Décision :** documents stockés dans PostgreSQL, vectorisés (pgvector), injectés par **RAG** dans le contexte de l'atelier concerné. Chaque risque doit citer **ses sources** (première parade contre l'hallucination).

### 4.4 Outils mis à disposition des agents

| Outil | Atelier concerné | Description |
|-------|------------------|-------------|
| `read_document` | Tous | Lire un document fourni par l'analyste (description du SI) |
| `search_knowledge_base` | Tous | Interroger la base RAG (EBIOS RM, ISO 27002…) |
| `lookup_cve` | Atelier 4 | Rechercher une CVE / score CVSS (NVD) |
| `search_attack_techniques` | Atelier 4 | Interroger MITRE ATT&CK pour le chemin d'attaque |
| `compute_risk_level` | Ateliers 3, 4 | Calculer le niveau à partir de gravité × vraisemblance |
| `validate_schema` | Orchestrateur | Vérifier qu'un JSON d'atelier est complet |

**Décision :** tous les outils sont **en lecture seule** (aucun agent ne modifie un SI réel). C'est une contrainte de sécurité non négociable.

### 4.5 Format des échanges entre ateliers

Chaque atelier lit exactement ce que le précédent a produit, sous forme de **JSON structuré**. Exemple de risque final :

```json
{
  "id": "R-07",
  "bien_essentiel": "Disponibilite du service de paiement",
  "evenement_redoute": "Indisponibilite du site marchand",
  "source_risque": "Attaquant externe (rancçongiciel)",
  "scenario_strategique": "S-03",
  "scenario_operationnel": "O-03-01",
  "gravite": "eleve",
  "vraisemblance": "moyenne",
  "niveau": "eleve",
  "traitement": "reduire",
  "mesures": ["Sauvegardes hors ligne", "Segmentation reseau"],
  "risque_residuel": "faible",
  "sources": ["EBIOS RM", "ISO 27002", "MITRE ATT&CK"],
  "valide_par": null
}
```

**Décision :** le champ `sources` est **obligatoire** ; le champ `valide_par` reste `null` tant qu'un humain n'a pas validé l'atelier.

---

## 5. Architecture détaillée

### 5.1 Vue globale du pipeline des 5 ateliers

```
Orchestrateur (LangGraph)
   │
   ├─► Atelier 1 · Cadrage & socle ──► biens, besoins DICP, événements redoutés, socle
   │      └─► [VALIDATION HUMAINE 1] ◄── correction / reprise ciblée
   │
   ├─► Atelier 2 · Sources de risques ──► sources de risques caractérisées
   │      └─► [VALIDATION HUMAINE 2]
   │
   ├─► Atelier 3 · Scénarios stratégiques ──► gravité × vraisemblance, cartographie
   │      └─► [VALIDATION HUMAINE 3]
   │
   ├─► Atelier 4 · Scénarios opérationnels ──► chemins d'attaque (MITRE ATT&CK)
   │      └─► [VALIDATION HUMAINE 4]
   │
   ├─► Atelier 5 · Traitement du risque ──► stratégies, mesures, risque résiduel
   │      └─► [VALIDATION HUMAINE 5]
   │
   └─► Compte rendu final (registre des risques + plan de traitement)
```

### 5.2 Fiche de chaque atelier (agent)

| Atelier / Agent | Reçoit | Fait | Produit |
|-----------------|--------|------|---------|
| **1 · Cadrage & socle** | Description du SI | Définit le périmètre, identifie biens essentiels/supports, besoins DICP, événements redoutés, socle de sécurité | Cadre de l'étude |
| **2 · Sources de risques** | Cadre de l'étude | Identifie et caractérise les sources de risques (objectif, motivation, capacité, biens visés, pertinence) | Liste des sources de risques |
| **3 · Scénarios stratégiques** | Événements redoutés + sources | Croise SR × événements redoutés, évalue gravité et vraisemblance | Scénarios stratégiques + cartographie |
| **4 · Scénarios opérationnels** | Scénarios stratégiques + biens supports | Décrit le chemin d'attaque concret, affine gravité/vraisemblance | Scénarios opérationnels |
| **5 · Traitement du risque** | Scénarios opérationnels notés | Choisit une stratégie, propose des mesures, évalue le risque résiduel | Plan de traitement + registre |
| **Orchestrateur** | Demande de l'analyste | Enchaîne les ateliers, gère les validations et les reprises | Historique complet |

Chaque atelier a sa **propre consigne (prompt)**, versionnée et stockée en base.

### 5.3 Structure du backend

```
backend/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration (pydantic-settings)
│   ├── database.py                # Connexion PostgreSQL (SQLAlchemy async)
│   ├── models/                    # Modèles ORM
│   │   ├── analysis.py            # Une étude EBIOS RM (cas SI)
│   │   ├── asset.py               # Biens essentiels / supports
│   │   ├── feared_event.py        # Événements redoutés
│   │   ├── risk_source.py         # Sources de risques
│   │   ├── scenario.py            # Scénarios stratégiques & opérationnels
│   │   ├── risk.py                # Risques (registre) + traitement
│   │   ├── workshop.py            # État et validation de chaque atelier
│   │   ├── agent_run.py           # Trace d'exécution d'un atelier
│   │   ├── knowledge.py           # Documents RAG
│   │   └── user.py
│   ├── schemas/                   # Schémas Pydantic (contrat JSON)
│   │   ├── asset.py
│   │   ├── feared_event.py
│   │   ├── risk_source.py
│   │   ├── scenario.py
│   │   ├── risk.py
│   │   └── analysis.py
│   ├── api/                       # Routeurs API
│   │   ├── analyses.py
│   │   ├── workshops.py
│   │   ├── risks.py
│   │   ├── agents.py
│   │   ├── knowledge.py
│   │   ├── reports.py
│   │   └── auth.py
│   ├── agents/                    # Le cœur du système (LangGraph)
│   │   ├── graph.py               # Graphe des 5 ateliers + validations
│   │   ├── orchestrator.py
│   │   ├── workshop1_framing.py   # Cadrage & socle
│   │   ├── workshop2_risk_sources.py
│   │   ├── workshop3_strategic.py
│   │   ├── workshop4_operational.py
│   │   ├── workshop5_treatment.py
│   │   ├── report.py              # Compte rendu final
│   │   ├── prompts.py             # Consignes versionnées de chaque atelier
│   │   └── state.py               # Typage de l'état partagé
│   ├── llm/
│   │   ├── base.py                # Interface LLMProvider
│   │   ├── opencode_go.py         # Adapter Opencode Go
│   │   └── factory.py
│   ├── tools/
│   │   ├── read_document.py
│   │   ├── knowledge_base.py      # RAG (pgvector)
│   │   ├── cve_lookup.py          # NVD API
│   │   ├── attack_techniques.py   # MITRE ATT&CK
│   │   └── risk_math.py           # compute_risk_level (gravité × vraisemblance)
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── report_generator.py    # Compte rendu → PDF/CSV/JSON
│   │   └── rag_service.py
│   ├── tasks/                     # Tâches Celery
│   │   └── analysis_tasks.py
│   └── utils/
│       ├── validators.py
│       └── logging.py             # Journalisation structurée JSON
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### 5.4 Structure du frontend

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   ├── analysis/              # Création d'une étude (description du SI)
│   │   ├── workshop/              # Vue d'un atelier + validation
│   │   ├── pipeline/              # Suivi des 5 ateliers (timeline)
│   │   ├── assets/                # Biens essentiels / supports
│   │   ├── risk-sources/          # Sources de risques
│   │   ├── scenarios/             # Scénarios stratégiques & opérationnels
│   │   ├── risk-register/         # Registre des risques + traitement
│   │   ├── validation/            # Écrans de validation humaine
│   │   └── report/                # Compte rendu final
│   ├── stores/                    # Zustand
│   ├── services/                  # Appels API + WebSocket
│   ├── router/
│   └── utils/
├── Dockerfile
├── tailwind.config.js
└── package.json
```

### 5.5 Schéma PostgreSQL

#### Table `analyses`
```json
{
  "id": "uuid",
  "name": "Boutique en ligne PME - 2026",
  "si_description": { "ecosysteme": "...", "flux": "...", "contexte_metier": "..." },
  "status": "in_progress",
  "current_workshop": 3,
  "started_at": "2026-09-01T08:00:00Z",
  "completed_at": null,
  "created_by": "user_uuid"
}
```

#### Table `assets` (biens essentiels / supports)
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "name": "Base de donnees clients",
  "kind": "bien_support",
  "besoins": ["confidentialite", "integrite"],
  "value": "eleve",
  "supports": "Processus de vente en ligne"
}
```

#### Table `feared_events` (événements redoutés)
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "label": "Indisponibilite du site marchand",
  "bien_essentiel_id": "uuid",
  "besoin": "disponibilite",
  "gravite": "eleve"
}
```

#### Table `risk_sources` (sources de risques)
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "type": "attaquant_externe",
  "objectif": "extorsion",
  "motivation": "financiere",
  "capacite": "eleve",
  "biens_vises": ["uuid"],
  "pertinence": "retenue"
}
```

#### Table `scenarios`
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "kind": "strategique",
  "identifiant": "S-03",
  "source_risque_id": "uuid",
  "evenement_redoute_id": "uuid",
  "gravite": "eleve",
  "vraisemblance": "moyenne",
  "niveau": "eleve",
  "detail_operationnel": null
}
```

#### Table `risks` (registre des risques)
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "scenario_id": "uuid",
  "identifiant": "R-07",
  "gravite": "eleve",
  "vraisemblance": "moyenne",
  "niveau": "eleve",
  "traitement": "reduire",
  "mesures": ["Sauvegardes hors ligne", "Segmentation reseau"],
  "risque_residuel": "faible",
  "sources": ["EBIOS RM", "ISO 27002", "MITRE ATT&CK"],
  "valide_par": null,
  "validated_at": null
}
```

#### Table `workshops` (état + validation par atelier)
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "numero": 2,
  "status": "awaiting_validation",
  "output": "{...}",
  "validated_by": null,
  "validated_at": null,
  "corrections": []
}
```

#### Table `agent_runs`
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "workshop": "workshop2_risk_sources",
  "prompt_version": "v1.2",
  "input_snapshot": "hash",
  "output": "{...}",
  "tokens_in": 1200,
  "tokens_out": 800,
  "duration_ms": 4500,
  "status": "success"
}
```

#### Table `knowledge_documents`
```json
{
  "id": "uuid",
  "title": "EBIOS Risk Manager - ANSSI",
  "source": "anssi-ebios-rm",
  "content": "...",
  "embedding": [0.01, -0.02],
  "updated_at": "2026-01-01T00:00:00Z"
}
```

#### Table `users`
```json
{
  "id": "uuid",
  "username": "analyste",
  "email": "analyste@example.com",
  "hashed_password": "$2b$12$...",
  "role": "analyst",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 6. API Endpoints

### Authentification
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/login` | Connexion (JWT) |
| POST | `/api/auth/register` | Inscription |
| GET | `/api/auth/me` | Profil utilisateur |
| POST | `/api/auth/refresh` | Rafraîchir token |

### Analyses (études EBIOS RM)
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/analyses` | Créer une étude (description du SI) |
| GET | `/api/analyses` | Liste des études |
| GET | `/api/analyses/{id}` | Détail + atelier courant |
| POST | `/api/analyses/{id}/start` | Lancer le pipeline des 5 ateliers |
| POST | `/api/analyses/{id}/stop` | Arrêter / annuler |
| DELETE | `/api/analyses/{id}` | Supprimer |

### Ateliers & validation humaine
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/analyses/{id}/workshops` | Liste des 5 ateliers + statuts |
| GET | `/api/analyses/{id}/workshops/{n}` | Sortie d'un atelier |
| POST | `/api/analyses/{id}/workshops/{n}/validate` | **Validation humaine** d'un atelier |
| POST | `/api/analyses/{id}/workshops/{n}/correct` | Correction + **reprise ciblée** de l'atelier |
| POST | `/api/analyses/{id}/workshops/{n}/retry` | Relancer l'atelier n |

### Biens / Sources / Scénarios / Risques
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/analyses/{id}/assets` | Biens essentiels et supports |
| GET | `/api/analyses/{id}/feared-events` | Événements redoutés |
| GET | `/api/analyses/{id}/risk-sources` | Sources de risques |
| GET | `/api/analyses/{id}/scenarios` | Scénarios stratégiques et opérationnels |
| GET | `/api/analyses/{id}/risks` | Registre des risques |
| PUT | `/api/analyses/{id}/risks/{risk_id}` | Correction manuelle d'un risque |

### Agents & traces
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/analyses/{id}/runs` | Historique d'exécution des ateliers |
| GET | `/api/agents` | Liste des ateliers-agents + consignes (prompts) |
| GET | `/api/agents/{name}/prompt` | Consigne versionnée d'un atelier |

### Base de connaissances
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/knowledge` | Liste des documents RAG |
| POST | `/api/knowledge` | Ajouter un document (admin) |
| DELETE | `/api/knowledge/{id}` | Supprimer un document (admin) |

### Compte rendu
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/analyses/{id}/report` | Générer le compte rendu final |
| GET | `/api/reports/{id}` | Télécharger le compte rendu (PDF/CSV/JSON) |

### Temps réel
| Méthode | Route | Description |
|---------|-------|-------------|
| WS | `/ws/analyses/{id}` | Suivi des ateliers + demandes de validation |

---

## 7. Sécurité détaillée

### 7.1 Authentification & autorisation

| Mécanisme | Implémentation |
|-----------|---------------|
| Hash des mots de passe | bcrypt (via `passlib`) |
| Tokens | JWT (`python-jose`), expiration configurable |
| Rôles | `admin` (gère tout + base de connaissances), `analyst` (crée/valide des études), `viewer` (lecture) |

### 7.2 Sécurité du système d'agents (risques propres à l'IA)

| Risque IA | Mesure implémentée |
|-----------|--------------------|
| **Hallucination** | Champ `sources` obligatoire, RAG sur documents officiels, validation humaine entre ateliers |
| **Injection de prompt** | Séparation stricte consignes/données, filtrage des entrées, consignes non modifiables par les données |
| **Fuite de données** | Cas d'étude 100 % fictifs ; couche `LLMProvider` prête à anonymiser si un jour nécessaire |
| **Excès d'autonomie** | Outils **lecture seule**, aucun accès à un SI réel, humain dans la boucle entre chaque atelier |
| **Empoisonnement** | Base de connaissances sourcée, contrôle des mises à jour, imports admin uniquement |
| **Dépendance fournisseur** | Couche d'abstraction `LLMProvider`, modèle remplaçable sans toucher aux agents |

Référence : **OWASP Top 10 for LLM Applications** (injection de prompt classée en tête).

### 7.3 Journalisation

| Événement | Niveau | Stockage |
|-----------|--------|----------|
| Étude démarrée/terminée | INFO | Table `agent_runs` + logs JSON |
| Atelier exécuté (entrée/sortie) | INFO | Table `agent_runs` (traçabilité) |
| Atelier validé/corrigé par un humain | INFO | Table `workshops` + logs |
| Reprise ciblée d'un atelier | INFO | Table `workshops` + logs |
| Échec d'appel LLM | ERROR | Logs + alerte |
| Tentative d'accès non autorisé | WARNING | Logs + alerte admin |
| Entrée suspecte (injection potentielle) | WARNING | Logs + filtrage |

### 7.4 Protection des données

- **Mots de passe** : hashés (bcrypt) — jamais stockés en clair.
- **Tokens JWT** : signés, durée de vie limitée.
- **Cas d'étude** : 100 % fictifs (aucune donnée réelle ni sensible).
- **Consignes des ateliers** : versionnées, modifiables uniquement par un admin.
- **PostgreSQL** : authentification activée, TLS recommandé.

---

## 8. Contraintes opérationnelles

### 8.1 Limites de ressources

| Ressource | Limite | Action si dépassée |
|-----------|--------|-------------------|
| Études simultanées | 3 max | File d'attente (Celery) |
| Durée max d'une étude | 45 minutes | Timeout + reprise possible |
| Tokens par appel LLM | Configurable | Troncature / résumé préalable |
| Taille de la description du SI | 50 Ko | Refus au lancement |
| Documents RAG | 1 000 max | Alerte admin |

### 8.2 Rétention des données

| Type de donnée | Durée de rétention | Action après expiration |
|----------------|--------------------|------------------------|
| Études (résultats) | 12 mois | Archivage puis purge |
| Traces d'exécution (`agent_runs`) | 6 mois | Purge |
| Comptes rendus exportés | 1 an | Archivage |
| Utilisateurs | Illimité | — |

---

## 9. Architecture asynchrone

Le déroulé des 5 ateliers (avec validations humaines) est long (de quelques minutes à plusieurs dizaines de minutes). L'architecture est asynchrone :

```
Client Web (React)
       │
       ▼
┌─────────────────┐   POST /api/analyses/{id}/start   ┌─────────────────┐
│   FastAPI        │◄────────────────────────────────│   Frontend      │
│   (API)          │── response {task_id} ───────────►│                 │
└────────┬────────┘                                   └─────────────────┘
         │ Envoie la tâche à Celery
         ▼
┌──────────────────────────────────────────────────────────────┐
│   Celery Worker → LangGraph (orchestrateur)                   │
│     Atelier 1 → [validation] → Atelier 2 → [validation]      │
│     → Atelier 3 → [validation] → Atelier 4 → [validation]    │
│     → Atelier 5 → [validation] → Compte rendu                │
└────────┬─────────────────────────────────────────────────────┘
         │ Stocke chaque sortie dans PostgreSQL
         ▼
┌─────────────────┐
│   PostgreSQL     │   (analyses, assets, scenarios, risks, workshops, agent_runs)
└─────────────────┘
         │
         │ Le frontend suit l'avancement via WebSocket
         ▼
┌─────────────────┐
│   WebSocket      │   statut de chaque atelier, logs, demande de validation
│   (FastAPI)      │
└─────────────────┘
```

Chaque **validation humaine** est un `interrupt` LangGraph : le pipeline s'arrête après l'atelier n, l'analyste valide/corrige dans l'interface, puis la **reprise est ciblée** (seul l'atelier impacté est relancé, les ateliers précédents sont conservés).

---

## 10. Docker & Déploiement

### 10.1 Services Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: risk_agents
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    depends_on: [postgres, redis]
    environment:
      DATABASE_URL: postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/risk_agents
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
      LLM_PROVIDER: opencode_go
      LLM_MODEL: ${LLM_MODEL}
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on: [postgres, redis]
    environment:
      DATABASE_URL: postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/risk_agents
      REDIS_URL: redis://redis:6379
      LLM_PROVIDER: opencode_go
      LLM_MODEL: ${LLM_MODEL}

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### 10.2 Pipeline CI/CD (GitHub Actions)

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: mypy backend/

  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env: { POSTGRES_USER: admin, POSTGRES_PASSWORD: test, POSTGRES_DB: risk_agents }
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v
      - run: npm ci && npm run test:unit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

---

## 11. Plan de développement (sprints)

### Sprint 1 : Fondations (semaine 1)
- [ ] Structure du projet backend + frontend
- [ ] Modèles PostgreSQL (SQLAlchemy + Alembic)
- [ ] Authentification JWT + rôles
- [ ] Couche `LLMProvider` (adapter Opencode Go) + mock pour tests
- [ ] Docker Compose + CI/CD de base

### Sprint 2 : Orchestrateur + Atelier 1 (semaine 2)
- [ ] Graphe LangGraph (squelette des 5 ateliers + 5 validations)
- [ ] Atelier 1 · Cadrage & socle (biens, besoins DICP, événements redoutés, socle)
- [ ] API analyses + workshop 1 + validation
- [ ] Interface : saisie du SI + vue cadrage

### Sprint 3 : Ateliers 2 & 3 (semaine 3)
- [ ] Atelier 2 · Sources de risques (caractérisation)
- [ ] Atelier 3 · Scénarios stratégiques (gravité × vraisemblance)
- [ ] Base de connaissances RAG (EBIOS RM, ISO 27005)
- [ ] Interface : sources de risques + cartographie

### Sprint 4 : Atelier 4 (semaine 4)
- [ ] Atelier 4 · Scénarios opérationnels (chemin d'attaque)
- [ ] Outils `lookup_cve` + `search_attack_techniques` (MITRE ATT&CK)
- [ ] Interface : vue scénarios opérationnels

### Sprint 5 : Atelier 5 + Compte rendu (semaine 5)
- [ ] Atelier 5 · Traitement du risque (stratégies, mesures, risque résiduel)
- [ ] Compte rendu final (PDF/CSV/JSON)
- [ ] Interface : registre des risques + compte rendu

### Sprint 6 : Validation humaine & reprises (semaine 6)
- [ ] `interrupt` LangGraph après chaque atelier
- [ ] API validate/correct/retry par atelier
- [ ] WebSocket de suivi + demandes de validation
- [ ] Interface : écrans de validation

### Sprint 7 : Finalisation (semaine 7)
- [ ] Tests unitaires + intégration (dont test d'injection de prompt)
- [ ] Cas de test complets (boutique en ligne, téléconsultation, réseau PME)
- [ ] Documentation technique + installation
- [ ] Audit sécurité (OWASP LLM)
- [ ] Déploiement final

---

## 12. Évolutions possibles (hors scope initial)

- Analyse de **documents annexes** (politiques, audits précédents) via RAG
- Export au format EBIOS RM officiel / conformité AI Act et RGPD
- Anonymisation/pseudonymisation automatique pour cas réels
- Aide au choix des mesures via rapprochement ISO 27002 ↔ ANSSI
- Génération de diagrammes DFD et de chemins d'attaque graphiques
- Alertes de re-validation quand un changement survient sur le SI

---

## 13. Critères de qualité

| Critère | Méthode de vérification |
|---------|------------------------|
| Conformité EBIOS RM | Les 5 ateliers suivent l'ordre et les livrables de la méthode |
| Architecture modulaire | Un atelier = un agent, contrats JSON clairs |
| Code maintenable | Ruff (lint), mypy (types), pytest (tests) |
| Tests automatisés | Couverture > 80 % (unitaires + intégration + tests d'injection de prompt) |
| Documentation API | Swagger/OpenAPI auto-généré + endpoint `/docs` |
| Traçabilité | Git + GitHub Projects + Issues + table `agent_runs` |
| Sécurité | Authentification, RBAC, outils lecture seule, humain dans la boucle, OWASP LLM |
| Qualité du registre | Chaque risque cite bien, événement redouté, source de risques, gravité, vraisemblance et source |
| Validation humaine | Une validation obligatoire entre chaque atelier |
| Docker | `docker compose up` = tout fonctionne |

---

## 14. Checklist de validation

Avant chaque push et fusion :

- [ ] `ruff check backend/` — aucun warning
- [ ] `mypy backend/` — aucun type error
- [ ] `pytest backend/tests/ -v` — tous verts
- [ ] `npm run lint` (frontend) — aucun warning
- [ ] `docker compose build` — succès
- [ ] `docker compose up` + vérification manuelle rapide
- [ ] Les 5 ateliers EBIOS RM s'enchaînent dans le bon ordre
- [ ] Une validation humaine est requise entre chaque atelier
- [ ] Chaque risque cite bien + événement redouté + source + gravité + vraisemblance + source
- [ ] Le compte rendu final est généré après validation de l'atelier 5
- [ ] Un test d'injection de prompt est passé avec succès
- [ ] Commit message explicite (convention : `type(scope): description`)
- [ ] CI verte sur la branche

