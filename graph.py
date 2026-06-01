from typing import TypedDict

from langgraph.graph import StateGraph, END

from agents.search_agent import search_web
from agents.research_agent import generate_research_summary
from agents.writer_agent import format_report
from agents.reader_agent import summarize_source


class ResearchState(TypedDict):
    query: str
    search_results: list
    processed_sources: list
    report: str
    formatted_report: str
    sources: list


def search_node(state: ResearchState):

    results = search_web(
        state["query"]
    )

    sources = [
        result["url"]
        for result in results[:3]
    ]

    return {
        "search_results": results,
        "sources": sources
    }

def reader_node(state: ResearchState):

    processed_sources = []

    for source in state["search_results"][:3]:

        processed_sources.append(
            summarize_source(source)
        )

    return {
        "processed_sources": processed_sources
    }


def research_node(state: ResearchState):

    report = generate_research_summary(
    query=state["query"],
    search_results=state["processed_sources"]
    )

    return {
        "report": report
    }


def writer_node(state: ResearchState):

    formatted_report = format_report(
        report=state["report"],
        query=state["query"],
        sources=state["sources"]
    )

    return {
        "formatted_report": formatted_report
    }


builder = StateGraph(ResearchState)

builder.add_node("search", search_node)
builder.add_node("reader", reader_node)
builder.add_node("research", research_node)
builder.add_node("writer", writer_node)

builder.set_entry_point("search")

builder.add_edge("search", "reader")
builder.add_edge("reader", "research")
builder.add_edge("research", "writer")
builder.add_edge("writer", END)

graph = builder.compile()