"""Squelette LangGraph du pipeline des 5 ateliers EBIOS RM.

Le graphe définit la structure du pipeline (5 ateliers enchaînés). L'exécution
réelle, avec validation humaine entre chaque atelier, est orchestrée par
`app.services.analysis_service` qui appelle les fonctions d'atelier une par une.
Ce graphe sert de référence structurelle et permet un déroulé complet « sec ».
"""

from langgraph.graph import END, START, StateGraph

from app.agents.state import AnalysisState
from app.agents.workshop1_framing import run_workshop_1
from app.agents.workshop2_risk_sources import run_workshop_2
from app.agents.workshop3_strategic import run_workshop_3
from app.agents.workshop4_operational import run_workshop_4
from app.agents.workshop5_treatment import run_workshop_5

WORKSHOP_FUNCTIONS = {
    1: run_workshop_1,
    2: run_workshop_2,
    3: run_workshop_3,
    4: run_workshop_4,
    5: run_workshop_5,
}


def _make_node(numero: int):
    async def node(state: AnalysisState) -> dict:
        output = await WORKSHOP_FUNCTIONS[numero](state)
        outputs = dict(state.get("workshop_outputs", {}))
        outputs[numero] = output
        return {"workshop_outputs": outputs, "current_workshop": numero}

    return node


def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("workshop_1", _make_node(1))
    graph.add_node("workshop_2", _make_node(2))
    graph.add_node("workshop_3", _make_node(3))
    graph.add_node("workshop_4", _make_node(4))
    graph.add_node("workshop_5", _make_node(5))

    graph.add_edge(START, "workshop_1")
    graph.add_edge("workshop_1", "workshop_2")
    graph.add_edge("workshop_2", "workshop_3")
    graph.add_edge("workshop_3", "workshop_4")
    graph.add_edge("workshop_4", "workshop_5")
    graph.add_edge("workshop_5", END)

    return graph.compile()


pipeline = build_graph()
