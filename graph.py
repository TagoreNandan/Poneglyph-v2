from typing import TypedDict

from langgraph.graph import StateGraph, END

from agents.search_agent import search_web
from agents.research_agent import generate_research_summary


class ResearchState(TypedDict):
    query: str
    search_results: list
    report: str


def search_node(state: ResearchState):

    results = search_web(
        state["query"]
    )

    return {
        "search_results": results
    }


def research_node(state: ResearchState):

    report = generate_research_summary(
        query=state["query"],
        search_results=state["search_results"]
    )

    return {
        "report": report
    }


builder = StateGraph(
    ResearchState
)

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "research",
    research_node
)

builder.set_entry_point(
    "search"
)

builder.add_edge(
    "search",
    "research"
)

builder.add_edge(
    "research",
    END
)

graph = builder.compile()