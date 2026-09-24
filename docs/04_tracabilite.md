# 4. Traçabilité

Chaque étape du pipeline produit des **traces vérifiables**.

## 4.1 Table `agent_runs` (témoin d'exécution)

| Champ | Contenu | Preuve |
|-------|---------|--------|
| `agent` | atelier exécuté | `app/services/analysis_service.py` (`run_workshop`) |
| `prompt_version` | version de la consigne (ex. `v1.1`) | `app/agents/prompts.py` (`WORKSHOP_PROMPTS`) |
| `input_snapshot` | **empreinte SHA-256** de l'état d'entrée | `analysis_service.py` (`_state_hash`) |
| `tokens_in` / `tokens_out` | consommation LLM | `llm/base.py` (`complete_structured`) + agents |
| `duration_ms` | durée de l'atelier | `analysis_service.py` |
| `status` | `success` ou **`failed`** | idem |
| `output` | sortie JSON de l'atelier | idem |

En cas d'échec d'un atelier, une trace `FAILED` est créée et l'étude passe en `failed`
(**plus jamais une étude bloquée sans explication**).

## 4.2 Validation humaine horodatée

- Ateliers : `workshops.validated_by` / `validated_at` (+ `corrections` stockées).
- Risques : `risks.valide_par` / `validated_at`.

## 4.3 Consignes versionnées

Chaque atelier utilise une consigne « système » versionnée (`WORKSHOP_PROMPTS`) et le
fournisseur de LLM est traçable (endpoint, modèle) : `app/config.py`, `app/llm/*`.

## 4.4 WebSocket (observabilité temps réel)

`/ws/analyses/{id}` diffuse les événements : `workshop_updated`, `workshop_validated`,
`analysis_completed` — preuve : `app/live.py`, `app/api/ws.py`, test `tests/unit/test_live.py`.