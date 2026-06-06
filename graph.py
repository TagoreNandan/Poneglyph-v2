from typing import TypedDict, Dict, Any

from langgraph.graph import StateGraph, END

from agents.search_agent import search_web
from agents.reader_agent import summarize_source
from agents.research_agent import generate_research_summary
from agents.writer_agent import format_report
from agents.critic_agent import review_report
from memory.database import save_research

from agents.router_agent import classify_query

from rag.retriever import retrieve
from agents.rag_answer_agent import generate_rag_answer

class ResearchState(TypedDict):
    query: str
    route: str

    search_results: list
    processed_sources: list

    rag_chunks: list
    rag_answer: str

    report: str

    critic_report: dict

    formatted_report: str

    insights: Dict[str, Any]

    sources: list

# -------------------------
# ROUTER
# -------------------------

def router_node(state: ResearchState):

    route = classify_query(
        state["query"]
    )

    print(
        f"\nROUTE SELECTED: {route}\n"
    )

    return {
        "route": route
    }


def route_decision(state: ResearchState):

    route = state["route"]

    if route == "WEB":
        return "search"

    elif route == "RAG":
        return "rag"
    
    elif route == "HYBRID":
        return "hybrid"

    else:
        return "search"

def critic_node(state: ResearchState):

    print("CRITIC NODE EXECUTED")

    critic_result = review_report(
        query=state["query"],
        report=state["report"]
    )

    return {
    "critic_report": critic_result,

    "insights": {
        "confidence_score":
            critic_result["confidence_score"],

        "source_quality":
            critic_result["source_quality"],

        "source_agreement":
            critic_result["source_agreement"],

        "coverage_score":
            critic_result["coverage_score"],

        "research_gaps":
            critic_result["research_gaps"],

        "contradictions":
            critic_result["contradictions"]
    }
}


# -------------------------
# WEB FLOW
# -------------------------

def search_node(state: ResearchState):
    print("SEARCH NODE EXECUTED")

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

    print("READER NODE EXECUTED")

    processed_sources = []

    for source in state["search_results"][:3]:

        processed_sources.append(
            summarize_source(source)
        )

    return {
        "processed_sources": processed_sources
    }


def research_node(state: ResearchState):

    print("RESEARCH NODE EXECUTED")

    report = generate_research_summary(
        query=state["query"],
        search_results=state["processed_sources"]
    )

    return {
        "report": report
    }


def writer_node(state: ResearchState):

    print(type(state.get("critic_report")))
    print(state.get("critic_report"))

    critic_data = state.get("critic_report")

    print("\nCRITIC DATA:\n")
    print(critic_data)
    print(type(critic_data))

    report_to_format = state["report"]
    
    report_to_format = state["report"]

    print(type(report_to_format))
    
    if isinstance(report_to_format, str):
        print(report_to_format[:500])


    formatted_report = format_report(
        report=report_to_format,
        query=state["query"],
        sources=state["sources"]
    )

    save_research(
        query=state["query"],
        route=state["route"],
        report=formatted_report
    )

    return {
    "formatted_report": formatted_report,
    "insights": state.get("insights", {})
}

# -------------------------
# RAG FLOW
# -------------------------

def rag_node(state: ResearchState):

    chunks = retrieve(
        state["query"]
    )

    answer = generate_rag_answer(
        state["query"],
        chunks
    )

    return {
        "rag_chunks": chunks,
        "rag_answer": answer
    }


def rag_writer_node(state: ResearchState):

    formatted_report = format_report(
        report=state["rag_answer"],
        query=state["query"],
        sources=[]
    )

    save_research(
        query=state["query"],
        route="RAG",
        report=formatted_report
    )

    return {
        "formatted_report": formatted_report
    }



def hybrid_node(state: ResearchState):

    web_results = search_web(
        state["query"]
    )

    rag_chunks = retrieve(
        state["query"]
    )

    combined_results = []

    # web results

    for result in web_results[:3]:

        combined_results.append(
            {
                "title": result["title"],
                "url": result["url"],
                "content": result.get(
                    "content",
                    ""
                )
            }
        )

    # rag results

    for chunk in rag_chunks:

        combined_results.append(
            {
                "title": "Local Knowledge Base",
                "url": "RAG",
                "content": chunk
            }
        )

    return {
        "processed_sources": combined_results,
        "sources": [
            result["url"]
            for result in web_results[:3]
        ]
    }


# -------------------------
# GRAPH
# -------------------------

builder = StateGraph(
    ResearchState
)

builder.add_node(
    "router",
    router_node
)

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "reader",
    reader_node
)

builder.add_node(
    "research",
    research_node
)

builder.add_node(
    "writer",
    writer_node
)

builder.add_node(
    "rag",
    rag_node
)

builder.add_node(
    "rag_writer",
    rag_writer_node
)

builder.add_node(
    "hybrid",
    hybrid_node
)

builder.add_node(
    "critic",
    critic_node
)

builder.set_entry_point(
    "router"
)

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "search": "search",
        "rag": "rag",
        "hybrid": "hybrid"
    }
)

# WEB PATH

builder.add_edge(
    "search",
    "reader"
)

builder.add_edge(
    "reader",
    "research"
)

# RAG PATH

builder.add_edge(
    "rag",
    "rag_writer"
)

builder.add_edge(
    "rag_writer",
    END
)

builder.add_edge(
    "hybrid",
    "research"
)


builder.add_edge(
    "research",
    "critic"
)

builder.add_edge(
    "critic",
    "writer"
)

builder.add_edge(
    "writer",
    END
)

graph = builder.compile()