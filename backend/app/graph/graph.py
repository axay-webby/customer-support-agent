from langgraph.graph import StateGraph, START, END

from backend.app.graph.state import GraphState
from backend.app.node.chatbot import (
    make_retrieve_node,
    retriever,
    memory_update,
    generate,
    kg_query,
    route_query,
)


def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)

    builder.add_node("router", route_query)
    builder.add_node("retrieve", make_retrieve_node(retriever))
    builder.add_node("kg_query", kg_query)
    builder.add_node("memory_update", memory_update)
    builder.add_node("generate", generate)

    builder.add_edge(START, "router")
    builder.add_edge("router", "memory_update")
    builder.add_conditional_edges(
        "router",
        lambda state: state.get("route", "retrieve"),
        {
            "retrieve": "retrieve",
            "kg_query": "kg_query",
        },
    )

    builder.add_edge("retrieve", "generate")
    builder.add_edge("kg_query", "generate")
    builder.add_edge("memory_update", "generate")
    builder.add_edge("generate", END)

    return builder

