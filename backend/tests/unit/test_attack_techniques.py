"""Tests de l'outil MITRE ATT&CK."""

from app.tools.attack_techniques import all_techniques, search_attack_techniques


def test_all_techniques_non_empty():
    techs = all_techniques()
    assert len(techs) > 10
    assert any(t["id"] == "T1190" for t in techs)


def test_search_by_tactic():
    results = search_attack_techniques(tactic="impact")
    assert results
    assert all(t["tactic"] == "impact" for t in results)


def test_search_by_keyword():
    results = search_attack_techniques(query="phishing")
    assert results
    assert any(t["id"] == "T1566" for t in results)
