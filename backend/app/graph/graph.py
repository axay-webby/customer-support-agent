from langgraph.graph import StateGraph, START, END

from backend.app.graph.state import GraphState
from backend.app.node.chatbot import make_retrieve_node, retriever, memory_update, generate, kg_query


def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)
 
    builder.add_node("retrieve", make_retrieve_node(retriever))
    builder.add_node("kg_query", kg_query)
    builder.add_node("memory_update", memory_update)
    builder.add_node("generate", generate)
 
    # Fan-out: both branches start from START and run concurrently
    builder.add_edge(START, "retrieve")
    builder.add_edge(START, "kg_query")
    builder.add_edge(START, "memory_update")
 
    # Fan-in: generate waits for both incoming edges before it fires
    builder.add_edge("retrieve", "generate")
    builder.add_edge("kg_query", "generate")
    builder.add_edge("memory_update", "generate")
 
    builder.add_edge("generate", END)
 
    return builder

