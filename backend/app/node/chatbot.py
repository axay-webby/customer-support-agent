from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.retrievers import BaseRetriever
from langgraph.store.base import BaseStore
from langgraph.config import get_store

from backend.app.service.llms import get_llm

from backend.app.core.config import PRODUCT_PDF_PATH
from backend.app.core.schema import MemoryDecision
from backend.app.db.knowladge_graph import create_cypher_chain, ingest_pdf_to_graph
from backend.app.graph.state import GraphState
from backend.app.service.system_prompt import customer_support_system_prompt, extract_memory_prompt
from backend.app.service.vector_store import create_retriever, should_refresh_pdf_assets


# Build / refresh the vector store based on the PDF fingerprint.
retriever = create_retriever(PRODUCT_PDF_PATH)

# Rebuild the knowledge graph if the PDF fingerprint changed.
force_refresh = should_refresh_pdf_assets(PRODUCT_PDF_PATH)
ingest_pdf_to_graph(PRODUCT_PDF_PATH, force_refresh=force_refresh)
cypher_chain = create_cypher_chain()


async def route_query(state: GraphState):
    llm = get_llm(streaming=False)
    messages = [
        SystemMessage(content=(
            "You are a routing assistant for a customer-support chatbot. "
            "Return only 'retrieve' for normal support questions about policies, troubleshooting, or product info. "
            "Return only 'kg_query' for questions about relationships, connections, dependencies, linked entities, or customer journeys."
        )),
        HumanMessage(content=state["question"]),
    ]

    result = await llm.ainvoke(messages)
    route = str(getattr(result, "content", "retrieve")).strip().lower()
    if route not in {"retrieve", "kg_query"}:
        route = "retrieve"

    return {"route": route}


# node 1: retrieve relevant chunks from the PDF
def make_retrieve_node(retriever: BaseRetriever | None):

    async def retrieve(state: GraphState):

        if retriever is None:
            return {"retrieved_docs": []}

        docs = await retriever.ainvoke(state['question'])
        return {"retrieved_docs": [d.page_content for d in docs]}

    return retrieve


async def kg_query(state: GraphState):
    
    if cypher_chain is None:
        return {"graph_context": []}

    try:
        result = await cypher_chain.ainvoke({"query": state['question']})
        answer = result.get("result", "")
        return {"graph_context": [answer] if answer else []} 

    except Exception:
        return {"graph_context": []}


# node 2: update memory (only adds facts, never overwrites with guesses)
MAX_MEMORY_ITEMS = 10

async def memory_update(state: GraphState):

    store: BaseStore = get_store()
    namespace = ("memory", state['thread_id'])
 
    existing = await store.aget(namespace, "facts")
    facts: list[str] = existing.value["facts"] if existing else []
 
    recent_facts = facts[-MAX_MEMORY_ITEMS:]
    existing_facts_text = "\n".join(recent_facts) if recent_facts else "None"
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(MemoryDecision)

    messages = [
        SystemMessage(content="You are a precise memory-extraction assistant."),
        HumanMessage(
            content=extract_memory_prompt.format(
                question=state["question"],
                existing_memory=existing_facts_text,
            )
        ),
    ]

    decision: MemoryDecision = await structured_llm.ainvoke(messages)

    if decision.should_write:
        new_facts = [m.text for m in decision.memories if m.is_new]
        if new_facts:
            facts = facts + new_facts
            await store.aput(namespace, "facts", {"facts": facts})
 
    return {"memory": facts}


# node 3: generate the final answer
async def generate(state: GraphState):

    context = "\n".join(state.get("retrieved_docs", []))
    memory = "\n".join(state.get("memory", []))

    llm = get_llm()
 
    messages = [
        SystemMessage(
            content=(
                customer_support_system_prompt.format(
                    context=context,
                    memory=memory
                )
            )
        ),
        HumanMessage(content=state['question']),
    ]
 
    result = await llm.ainvoke(messages)
    return {"response": result.content}
