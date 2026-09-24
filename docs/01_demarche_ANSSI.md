# 1. Démarche & alignement ANSSI

L'outil met en œuvre la méthode **EBIOS Risk Manager** de l'ANSSI. Cette section montre
comment chaque exigence méthodologique est alignée, et les preuves associées.

## 1.1 Méthode retenue : EBIOS Risk Manager (justification)

Un modèle a été choisi et justifié (exigence du sujet) : **EBIOS Risk Manager**.
Justification : méthode officielle ANSSI, structurée en ateliers, cohérente avec les
référentiels ISO ; c'est le modèle par défaut le plus adapté à une analyse de SI (vs STRIDE
orienté applications, vs LINDDUN orienté vie privée).

## 1.2 Les 5 ateliers (mapping avec la méthode)

| Atelier EBIOS RM | Contenu implémenté | Preuve (code) |
|------------------|--------------------|---------------|
| 1 · Cadrage & socle de sécurité | périmètre, biens essentiels/supports, besoins **DICP**, événements redoutés, socle (avec écarts) | `backend/app/agents/workshop1_framing.py`, consigne `WORKSHOP1_SYSTEM` (`app/agents/prompts.py`) |
| 2 · Sources de risques | menaces **intentionnelles** et couples **source de risque / objectif visé (SR/OV)**, motivation, ressources, activité, pertinence | `workshop2_risk_sources.py`, `WORKSHOP2_SYSTEM` |
| 3 · Scénarios stratégiques | **parties prenantes** critiques + scénarios cotés en **gravité seule** | `workshop3_strategic.py`, `WORKSHOP3_SYSTEM` |
| 4 · Scénarios opérationnels | chemins d'attaque (MITRE ATT&CK), **vraisemblance V1-V4 évaluée ici**, affinage gravité | `workshop4_operational.py`, `WORKSHOP4_SYSTEM` |
| 5 · Traitement du risque | stratégie (réduire/transférer/éviter/accepter), mesures, **risque résiduel**, plan | `workshop5_treatment.py`, `WORKSHOP5_SYSTEM` |

Conformité au guide ANSSI :
- sinistres et erreurs non intentionnels **renvoyés au socle** (Atelier 1), conformément à la
  méthode (les ateliers 2-4 portent sur les menaces) ;
- la **vraisemblance** est évaluée à l'Atelier 4 (sur les scénarios opérationnels), pas trop tôt.

## 1.3 Échelles G1-G4 / V1-V4 et matrice 4×4

- Gravité `g1…g4`, vraisemblance `v1…v4` (énums `app/models/enums.py`).
- Niveau de risque = **matrice déterministe** gravité × vraisemblance, calculée dans le code
  (`app/tools/risk_math.py`) et non par le LLM — reproductible et justifiable.

```
Preuve : tests/unit/test_risk_math.py (coins + mi-échelle).
```

## 1.4 Référentiels intégrés (base de connaissances RAG)

| Référentiel | Usage | Preuve |
|-------------|-------|--------|
| EBIOS RM (ANSSI) | typologie des sources, scénarios | `app/services/rag_service.py` (`SEED_DOCUMENTS`) |
| ISO/IEC 27005 | appréciation du risque | idem |
| ISO/IEC 27002 | catalogue de mesures (Ateliers 1 & 5) | idem |
| Guides ANSSI (hygiène informatique) | mesures | idem |
| MITRE ATT&CK | techniques d'attaque (Atelier 4) | `app/tools/attack_techniques.py` |

## 1.5 Vocabulaire et pivots méthodologiques

- Besoins de sécurité **DICP** exposés par l'Atelier 1 (schémas `app/schemas/workshop.py`).
- Couples SR/OV construits (Atelier 2), parties prenantes et criticité de l'écosystème (Atelier 3).
- Registre des risques conforme au format attendu : actif, menace/événement, niveau,
  traitement, mesures, **sources**, validation (**`valide_par`**).

> Consensus de simplification assumé (documenté) : échelles G1-G4/V1-V4 simplifiées de la
> granularité exacte du guide, socle synthétisé. Précision et justifications dans
> `[DOCUMENTATION_TECHNIQUE.md](DOCUMENTATION_TECHNIQUE.md)` (section 9).