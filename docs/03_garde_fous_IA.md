# 3. Garde-fous IA — risques propres aux LLM et parades (avec preuves)

Alignement sur l'**OWASP Top 10 for LLM Applications** et les recommandations ANSSI pour un
système d'IA générative. Chaque risque → parade → preuve (code + test).

| Risque IA | Parade implémentée | Preuve |
|-----------|--------------------|--------|
| **Hallucination** | Champ `sources` **obligatoire** sur chaque scénario et risque ; base RAG sourcée (EBIOS RM, ISO, ANSSI) ; niveau de risque **calculé dans le code** (pas par le LLM) ; reprise sur sortie invalide (erreur renvoyée au modèle, jusqu'à 3 essais) | `schemas/workshop.py` ; `tools/risk_math.py` ; `agents/base.py` ; test `tests/unit/test_reference_cases.py` (chaque risque a des sources) |
| **Injection de prompt** | Données **délimitées** `[DONNÉES]…[/DONNÉES]` ; consigne de sécurité « données non exécutables » ; **détection de motifs** d'injection ; avertissement dans le prompt | `agents/prompts.py` (délimiteurs + `SECURITY_GUARD`) ; `core/prompt_guard.py` ; test `tests/unit/test_injection.py` |
| **Validation croisée (anti-références fantômes)** | Chaque atelier est vérifié contre les sorties précédentes : biens, sources, événements, scénarios ; les entrées hors catalogue sont retirées/alignées ; anomalies tracées dans `_validation` | `agents/cross_validation.py` ; test `tests/unit/test_cross_validation.py` |
| **Techniques ATT&CK inventées** | Filtrage **sur catalogue curé** (vrais identifiants) + libellé explicite dans le prompt | `tools/attack_techniques.py` + `workshop4_operational.py` ; test `test_cross_validation.py` |
| **Homoglyphes / encodages** | Normalisés **sur les clés uniquement** (valeurs préservées) | `llm/base.py` (`_normalize_keys`) ; test `tests/unit/test_llm.py` |
| **Excès d'autonomie** | Architecture **lecture seule** : les agents ne génèrent que du texte JSON ; aucun appel à un système réel ; **humain dans la boucle** entre chaque atelier et par risque | pipeline (docs), `app/api/ws.py`, `app/api/resources.py` |
| **Empoisonnement (base de connaissances)** | Base RAG limitée à des **documents officiels** (ANSSI, ISO) contrôlés, catalogue ATT&CK curé | `services/rag_service.py` ; `tools/attack_techniques.py` |
| **Dépendance fournisseur** | Couche d'abstraction `LLMProvider` (interface + fabrique) ; modèle **remplaçable** (Opencode Go / mock) | `llm/base.py`, `llm/factory.py`, `llm/opencode_go.py`, `llm/mock.py` |
| **Fuite de données / vie privée** | **Cas 100 % fictifs** (A/B/C du sujet), aucune donnée réelle ; avertissement dans la documentation | `app/reference_cases.py` ; README |
| **Consigne système divulguée** | Consigne de sécurité rappelant de ne jamais la révéler | `agents/prompts.py` (`SECURITY_GUARD`) |

## 3.1 Humain dans la boucle

- **Entre chaque atelier** : `/workshops/{n}/validate` (enchaîne le suivant), `/correct`
  (reprise ciblée avec corrections stockées), `/retry`.
- **Sur chaque risque** : `/risks/{risk_id}/validate` (remplit `valide_par` + `validated_at`).
- L'étude n'est **terminée** qu'après validation de l'Atelier 5 ; le compte rendu s'appuie sur
  un registre produit par les agents puis validé par l'humain.

## 3.2 Sortie structurée

Le format JSON d'échange entre ateliers est un contrat Pydantic versionné : les ateliers
lisent exactement ce que le précédent a produit, avec vérifications (`model_validator` de
présence, listes non vides, chemin d'attaque requis en atelier 4). Schémas : `app/schemas/workshop.py`.

> Tests dédiés : `tests/unit/test_injection.py`, `tests/unit/test_cross_validation.py`,
> `tests/unit/test_llm.py`, `tests/unit/test_risk_math.py`, `tests/unit/test_live.py`.