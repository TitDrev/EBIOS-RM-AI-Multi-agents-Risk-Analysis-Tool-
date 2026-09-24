# OBJECTIF

Tu es un architecte logiciel senior spécialisé en gestion des risques (méthode EBIOS Risk Manager de l'ANSSI, ISO 27005, ISO 27002, MITRE ATT&CK), systèmes multi-agents IA (LangGraph, RAG) et développement d'applications web de sécurité.

Je veux construire un système multi-agents complet qui automatise la réalisation des 5 ateliers d'EBIOS Risk Manager sur n'importe quel système d'information.

Le système doit prendre en entrée la description d'un SI (écosystème, flux de données, contexte métier) et dérouler les 5 ateliers, avec une validation humaine entre chaque atelier, pour produire un compte rendu final.

Le but :
« un SI en entrée = 5 ateliers EBIOS RM validés = compte rendu argumenté », l'humain restant décideur.

---

# CONTRAINTES IMPORTANTES

---

Le système ne doit PAS :

* inventer des risques ou des sources sans source (hallucinations)
* sauter une validation humaine entre deux ateliers
* remplacer l'analyste : l'humain valide chaque étape
* agir sur un système réel (aucun agent ne modifie quoi que ce soit)
* exposer des données réelles et sensibles
* se coupler à un seul fournisseur de LLM

Le système DOIT :

* être générique : dérouler les 5 ateliers sur n'importe quel SI
* être multi-agents : un agent spécialisé par atelier, orchestré
* structurer les échanges entre ateliers (JSON)
* exiger des sources pour chaque risque
* imposer une validation humaine entre chaque atelier
* produire un compte rendu final (registre des risques + plan de traitement)
* tracer et journaliser toutes les actions

---

# RAPPEL : LES 5 ATELIERS EBIOS RM

---

1. ATELIER 1 · CADRAGE ET SOCLE DE SÉCURITÉ
   * définir le périmètre de l'étude
   * identifier les biens essentiels (valeurs métier) et biens supports
   * identifier les besoins de sécurité (DICP : Disponibilité, Intégrité, Confidentialité, Traçabilité)
   * identifier les événements redoutés
   * établir le socle de sécurité (mesures existantes / prévues)
   * définir les échelles de gravité et de vraisemblance

2. ATELIER 2 · SOURCES DE RISQUES
   * identifier les sources de risques (attaquants, internes malveillants/négligents, sinistres)
   * caractériser chacune : objectif, motivation, capacité, biens visés, pertinence

3. ATELIER 3 · SCÉNARIOS STRATÉGIQUES
   * croiser sources de risques × événements redoutés
   * évaluer gravité et vraisemblance
   * produire la cartographie des risques

4. ATELIER 4 · SCÉNARIOS OPÉRATIONNELS
   * décrire le chemin d'attaque concret (biens supports, techniques MITRE ATT&CK)
   * affiner gravité et vraisemblance

5. ATELIER 5 · TRAITEMENT DU RISQUE
   * choisir une stratégie : réduire / transférer / éviter / accepter
   * proposer des mesures (ISO 27002, guides ANSSI)
   * évaluer le risque résiduel
   * produire le plan de traitement

---

# STACK TECHNIQUE SOUHAITEE

---

Backend :

* Python 3.11+ / FastAPI
* orchestration d'agents : LangGraph (LangChain)
* architecture async, workers, queue jobs

IA :

* LLM : modèles Opencode Go via une couche d'abstraction (LLMProvider)
* RAG : base de connaissances (EBIOS RM, ISO 27005, ISO 27002, ANSSI, MITRE ATT&CK)
* outils en lecture seule (recherche CVE/CVSS, techniques ATT&CK, calcul de niveau, lecture de documents)

Frontend :

* React 18 + TypeScript + Tailwind
* UI claire : suivi des ateliers, validation, registre des risques, compte rendu

Base de données :

* PostgreSQL + pgvector (données relationnelles + embeddings)

Cache / files :

* Redis + Celery

Containerisation :

* Docker + docker-compose

Observabilité :

* structured logs JSON
* traces d'exécution des ateliers (entrée/sortie, prompt, tokens, durée)

---

# ARCHITECTURE ATTENDUE

---

Je veux une architecture modulaire :

agents/
  orchestrator/
  workshop1-framing/          # Atelier 1 : cadrage & socle de sécurité
  workshop2-risk-sources/     # Atelier 2 : sources de risques
  workshop3-strategic/        # Atelier 3 : scénarios stratégiques
  workshop4-operational/      # Atelier 4 : scénarios opérationnels
  workshop5-treatment/        # Atelier 5 : traitement du risque
  report/                     # Compte rendu final
  validation/                 # Humain dans la boucle (entre chaque atelier)
llm/                          # abstraction LLMProvider (Opencode Go)
tools/                        # read_document, knowledge_base, cve_lookup, attack_techniques, risk_math
knowledge/                    # base RAG (documents sourcés)
memory/                       # état partagé structuré (JSON)
services/                     # analyse, reporting, rag
api/                          # FastAPI routes
queue/                        # Celery tasks
websocket/                    # suivi temps réel du pipeline
exports/                      # PDF / CSV / JSON

---

# PIPELINE GLOBAL ATTENDU

---

1. ANALYSTE SAISIT LA DESCRIPTION DU SI
   * écosystème (composants, serveurs, services)
   * flux de données
   * contexte métier et contraintes (RGPD…)
   * documents annexes optionnels

2. ORCHESTRATEUR (LangGraph)
   * enchaîne les 5 ateliers dans l'ordre
   * s'arrête après chaque atelier pour validation humaine
   * fait circuler les résultats (état partagé JSON)
   * conserve l'historique complet

3. ATELIER 1 · CADRAGE & SOCLE (agent)
   * produit : périmètre, biens essentiels/supports, besoins DICP, événements redoutés, socle de sécurité, échelles gravité/vraisemblance

4. VALIDATION HUMAINE 1
   * l'analyste relit, corrige, valide ou relance l'atelier 1

5. ATELIER 2 · SOURCES DE RISQUES (agent)
   * produit : sources de risques caractérisées (objectif, motivation, capacité, biens visés, pertinence)

6. VALIDATION HUMAINE 2

7. ATELIER 3 · SCÉNARIOS STRATÉGIQUES (agent)
   * produit : scénarios stratégiques + cartographie (gravité × vraisemblance)

8. VALIDATION HUMAINE 3

9. ATELIER 4 · SCÉNARIOS OPÉRATIONNELS (agent)
   * produit : chemins d'attaque détaillés, gravité/vraisemblance affinées

10. VALIDATION HUMAINE 4

11. ATELIER 5 · TRAITEMENT DU RISQUE (agent)
    * produit : stratégies, mesures, risque résiduel, plan de traitement

12. VALIDATION HUMAINE 5

13. COMPTE RENDU FINAL
    * registre des risques validé
    * plan de traitement
    * justification de la démarche
    * export PDF / CSV / JSON

---

# FORMAT DES ÉCHANGES

---

Chaque atelier lit et produit du JSON structuré :

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

Contraintes :

* le champ `sources` est obligatoire (parade contre l'hallucination)
* le champ `valide_par` reste `null` tant qu'un humain n'a pas validé l'atelier
* `validate_schema` vérifie automatiquement que rien ne manque
* la sortie de chaque atelier est stockée avec son statut de validation

---

# FICHES DES ATELIERS (AGENTS)

---

Créer pour chaque atelier :

* une consigne (prompt) versionnée : rôle, tâche EBIOS RM, format de sortie attendu
* la liste des outils autorisés (moindre privilège)
* le contrat d'entrée/sortie (JSON)

Créer :

class WorkshopSpec          # rôle, prompt versionné, outils, contrat I/O
class AgentRun              # trace d'exécution (entrée, sortie, tokens, durée, statut)
class AnalysisState         # état partagé typé (LangGraph TypedDict)
class OrchestratorGraph     # graphe LangGraph + interrupt après chaque atelier
class ValidationResult      # décision humaine (valider / corriger / relancer)

---

# FEATURES IMPORTANTES

---

Je veux :

* enchaînement des 5 ateliers tracé pas à pas
* validation humaine obligatoire entre chaque atelier
* reprise ciblée (corriger l'atelier n sans refaire les précédents)
* suivi temps réel via WebSocket (statut de chaque atelier, logs)
* registre des risques filtrable et triable
* cartographie gravité × vraisemblance
* chemins d'attaque (scénarios opérationnels) visualisés
* compte rendu final (PDF / CSV / JSON)
* historique des études et comparaison
* base de connaissances administrable (RAG)
* gestion des consignes (prompts) versionnées

---

# UX/UI

---

UX ultra simple :
« Décrire le SI -> Lancer l'analyse »

Puis :

* timeline des 5 ateliers + 5 validations
* biens essentiels et supports
* sources de risques
* cartographie gravité × vraisemblance
* scénarios opérationnels (chemins d'attaque)
* registre des risques + traitement
* validation humaine (valider / corriger) à chaque étape
* compte rendu final
* détails techniques collapsibles (sources, justification, traces)

Mode :

* Beginner : zéro configuration, cas d'étude pré-remplis
* Advanced : choix des échelles, consignes personnalisables

---

# SECURITE

---

Le système doit :

* outils en lecture seule (aucun agent n'agit sur un SI réel)
* humain dans la boucle (validation entre chaque atelier)
* séparer strictement consignes et données (anti injection de prompt)
* filtrer les entrées suspectes
* exiger des sources pour chaque risque (anti hallucination)
* couche LLMProvider remplaçable (anti dépendance fournisseur)
* base de connaissances sourcée et contrôlée (anti empoisonnement)
* journalisation complète des actions
* secrets management (clés LLM en variables d'environnement)

---

# PERFORMANCE

---

Je veux :

* exécution asynchrone (Celery) pour les études longues
* reprises ciblées (ne pas tout relancer)
* cache RAG (embeddings pré-calculés)
* rate limiting des appels LLM
* parallélisation des scénarios par bien quand possible
* timeout strict par appel LLM

---

# TESTS

---

Créer :

* unit tests (chaque atelier, calcul de niveau, validation de schéma)
* integration tests (déroulé complet des 5 ateliers sur un cas)
* tests d'injection de prompt (document piégé -> l'atelier ne doit pas dévier)
* tests d'hallucination (vérifier que `sources` est toujours rempli)
* tests de validation humaine (le pipeline s'arrête entre chaque atelier)
* tests de reprise ciblée
* e2e tests (UI)

Créer les cas d'étude de référence :

* A · Boutique en ligne (PME)
* B · Téléconsultation médicale
* C · Réseau d'une PME

Pour chaque cas : une analyse EBIOS RM de référence faite à la main sert de vérité terrain pour juger les ateliers.

---

# LIVRABLES ATTENDUS

---

Je veux :

1. architecture complète
2. arborescence projet
3. modèles DB (PostgreSQL)
4. diagrammes (pipeline, graphe des ateliers)
5. workflow EBIOS RM
6. fiches et consignes (prompts) de chaque atelier
7. code production-ready
8. APIs REST
9. websocket events
10. workers Celery
11. docker compose
12. CI/CD
13. tests
14. UI screens
15. stratégie sécurité (OWASP LLM)
16. roadmap future

---

# IMPORTANT

---

Je ne veux PAS :

* pseudo code vague
* exemples incomplets
* MVP bricolé
* architecture amateur

Je veux :

* code propre
* vraie architecture production
* réflexion sécurité (OWASP Top 10 for LLM Applications)
* réflexion UX
* réflexion gestion des risques (vocabulaire EBIOS RM juste, ateliers respectés)
* réflexion maintenabilité

Chaque décision doit être justifiée techniquement.

Commencer par :

1. architecture globale
2. choix techniques argumentés
3. diagrammes
4. pipeline détaillé des 5 ateliers
5. structure dossiers
6. modèles données
7. graphe LangGraph + fiches des ateliers
8. puis implémentation complète
