"""Outil de recherche de CVE via l'API NVD (NIST).

En cas d'échec réseau ou d'absence de clé, retourne une liste vide (mode dégradé).
Utilisé par les ateliers pour justifier des scénarios par des vulnérabilités connues.
"""

import httpx

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


async def lookup_cve(keyword: str, limit: int = 5) -> list[dict]:
    """Recherche des CVE par mot-clé et retourne une liste de résumés."""
    params: dict[str, str | int] = {"keywordSearch": keyword, "resultsPerPage": limit}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(NVD_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return []

    results = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")
        descriptions = cve.get("descriptions", [])
        description = next(
            (d.get("value", "") for d in descriptions if d.get("lang") == "en"),
            "",
        )
        metrics = cve.get("metrics", {})
        cvss = _extract_cvss(metrics)
        results.append(
            {"cve_id": cve_id, "description": description[:300], "cvss": cvss}
        )
    return results


def _extract_cvss(metrics: dict) -> float | None:
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2"):
        for m in metrics.get(key, []):
            score = m.get("cvssData", {}).get("baseScore")
            if score is not None:
                return float(score)
    return None
