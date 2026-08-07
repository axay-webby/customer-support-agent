from langgraph.graph import StateGraph, START, END

from backend.app.graph.state import GraphState
from backend.app.node.chatbot import (
    make_retrieve_node,
    retriever,
    memory_update,
    generate,
    kg_query,
)


async def combine_results(state: GraphState):
    retrieved_docs = state.get("retrieved_docs", [])
    graph_context = state.get("graph_context", [])

    combined_context = [
        *[doc for doc in retrieved_docs if doc],
        *[context for context in graph_context if context],
    ]

    return {"combined_context": combined_context}


def build_context_subgraph() -> StateGraph:
    builder = StateGraph(GraphState)

    builder.add_node("retrieve", make_retrieve_node(retriever))
    builder.add_node("kg_query", kg_query)
    builder.add_node("combine_results", combine_results)

    builder.add_edge(START, "retrieve")
    builder.add_edge(START, "kg_query")
    builder.add_edge("retrieve", "combine_results")
    builder.add_edge("kg_query", "combine_results")
    builder.add_edge("combine_results", END)

    return builder


def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)

    context_subgraph = build_context_subgraph().compile()
    builder.add_node("context_subgraph", context_subgraph)
    builder.add_node("memory_update", memory_update)
    builder.add_node("generate", generate)

    builder.add_edge(START, "context_subgraph")
    builder.add_edge("context_subgraph", "memory_update")
    builder.add_edge("memory_update", "generate")
    builder.add_edge("generate", END)

    return builder

