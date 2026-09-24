# 5. Conformité au sujet E21 — matrice critères → preuves

Reprise exhaustive du sujet (`E21_Management_de_la_sécurité_—_Projet_Agents_IA_pour_l'analyse_de_risques.pdf`).
Légende : ✅ implémenté et testé · 🟡 partiel ou à compléter par l'équipe · ⬜ livrable humain restant.

---

## 5.1 La liste de contrôle du sujet (7 questions)

| # | Question du sujet | Statut | Preuve / emplacement |
|---|-------------------|--------|----------------------|
| 1 | Chaque risque du registre cite-t-il un **actif, une menace, un niveau et une source** ? | ✅ | `schemas/workshop.py` (`RisqueTraite` : bien_essentiel, evenement_redoute, niveau, **sources** obligatoires) ; test `tests/integration/test_reference_cases.py` (assert : chaque risque a des `sources`) |
| 2 | Le choix du **modèle de menaces** est-il justifié par le cas étudié ? | ✅ | Choix **EBIOS RM** justifié → [01_demarche_ANSSI.md §1.1](01_demarche_ANSSI.md) ; consignes `WORKSHOP2/3/4_SYSTEM` |
| 3 | Un **humain a-t-il validé chaque risque** avant le rendu ? | ✅ | Validation **par risque** `/risks/{id}/validate` (`app/api/resources.py`) + validation **par atelier** ; étude terminée seulement après validation de l'Atelier 5 ; test `test_reference_cases.py` |
| 4 | Avez-vous **comparé** le résultat des agents à **votre propre analyse** ? | ⬜ | Analyse manuelle de référence **à rédiger par l'équipe** ; l'outil fournit les cas A/B/C (`app/reference_cases.py`) et un point de comparaison possible (compte rendu JSON) |
| 5 | Avez-vous testé ce qui se passe si un document contient une **consigne piégée** ? | ✅ | Protection + tests : `app/core/prompt_guard.py`, `app/agents/prompts.py` (délimiteurs + `SECURITY_GUARD`), **`tests/unit/test_injection.py`** |
| 6 | **Aucune donnée réelle et sensible** n'a-t-elle été envoyée à un service IA externe ? | ✅ | **Cas 100 % fictifs** (`app/reference_cases.py`) ; pas de jeux de données réels ; note « docteur » dans README & doc technique |
| 7 | Les **outils d'IA utilisés** sont-ils cités dans le dossier ? | ✅ | README « Outils IA utilisés » + `docs/DOCUMENTATION_TECHNIQUE.md` §9 (deepseek-v4-pro via Opencode Go, assistance code, bibliothèques) |

---

## 5.2 Critères d'évaluation (pondérations fixées par l'enseignant)

| Critère | Attendu | Statut | Élément de preuve |
|---------|---------|--------|-------------------|
| **Maîtrise de la démarche de risque** | Vocabulaire juste, étapes respectées, registre cohérent | ✅ | 5 ateliers EBIOS RM (ordre imposé), besoin DICP, SR/OV, G1-G4/V1-V4 ; [01_demarche_ANSSI.md](01_demarche_ANSSI.md) |
| **Qualité de l'architecture** | Rôles clairs, échanges structurés, orchestrateur pertinent | ✅ | Un agent par atelier, contrats Pydantic JSON, validation croisée ; [DOCUMENTATION_TECHNIQUE.md](DOCUMENTATION_TECHNIQUE.md) §1-3 |
| **Choix et justification du modèle** | Modèle adapté et justifié | ✅ | [01_demarche_ANSSI.md §1.1](01_demarche_ANSSI.md) |
| **Sécurité du système d'agents** | Risques de l'IA identifiés et traités | ✅ | [03_garde_fous_IA.md](03_garde_fous_IA.md) (OWASP LLM Top 10) + [02_securite_applicative.md](02_securite_applicative.md) |
| **Esprit critique** | Comparaison avec l'analyse manuelle, limites expliquées | 🟡 | Limites documentées (doc technique §9) ; **comparaison agents/humain à rédiger** (Équipe) |
| **Restitution** | Dossier clair, démonstration, réponses aux questions | 🟡 | Outil démontrable + tests ; **dossier & soutenance à préparer** (Équipe) |

---

## 5.3 Les 3 livrables du sujet

### 1) Dossier écrit
| Élément attendu | Statut | Où / à faire |
|-----------------|--------|--------------|
| Description du cas étudié | 🟡 | Cas A/B/C prêts (`app/reference_cases.py`) ; **description 1 page par cas à rédiger** |
| Architecture et fiche de chaque agent | ✅ | `docs/DOCUMENTATION_TECHNIQUE.md` ; fiche des 5 ateliers (reçoit / fait / produit) dans [01_demarche_ANSSI.md §1.2](01_demarche_ANSSI.md) |
| Consignes (prompts) utilisées | ✅ | `app/agents/prompts.py` (`WORKSHOP*_SYSTEM`, versionnées) |
| Registre des risques obtenu | ✅ | Généré par l'Atelier 5, persisté (`risks`), exportable JSON/CSV/PDF |
| Analyse critique des résultats | ⬜ | **À rédiger par l'équipe** (aide : limites déjà documentées) |

### 2) Prototype / maquette
| Élément attendu | Statut | Où |
|-----------------|--------|----|
| Code | ✅ | `backend/`, `frontend/` |
| Exemple d'exécution sur le cas | ✅ | `backend/scripts/smoke_llm.py` + tests de référence (A/B/C) |
| Traces des échanges entre agents | ✅ | Table `agent_runs` (prompt versionné, tokens, hash, sortie) → [04_tracabilite.md](04_tracabilite.md) |

### 3) Soutenance (45 min)
| Élément | Statut | Où / à faire |
|---------|--------|--------------|
| Présentation de l'architecture | 🟡 | Slides **à préparer** ; support fourni (docs + README) |
| Démonstration | ✅ | Application fonctionnelle (docker compose / uvicorn) |
| Ce qui marche, ce qui ne marche pas | 🟡 | Limites documentées ; **oral à préparer** |
| Les risques de votre propre système | ✅ | [03_garde_fous_IA.md](03_garde_fous_IA.md) + [02_securite_applicative.md](02_securite_applicative.md) |

---

## 5.4 Jalons du projet

| Jalon | État |
|-------|------|
| Cadrer (choix du cas, description) | ✅ cas A/B/C fournis en données |
| Concevoir (architecture, fiches, consignes) | ✅ |
| Prototyper (chaîne fonctionnelle) | ✅ |
| Tester (comparaison + injection) | ✅ (injection/croisement testés) · 🟡 comparaison manuelle à faire |
| Restituer (dossier + soutenance) | 🟡 en attente de l'équipe |

## 5.5 Risques propres à l'IA (chapitre du sujet)

Tous couverts et prouvés : hallucination, injection de prompt, fuite de données, excès
d'autonomie, empoisonnement, dépendance → [03_garde_fous_IA.md](03_garde_fous_IA.md).