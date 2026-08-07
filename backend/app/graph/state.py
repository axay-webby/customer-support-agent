from typing import TypedDict, Annotated
from operator import add


class GraphState(TypedDict):

    question: str
    thread_id: str

    # written by `retrieve`
    retrieved_docs: Annotated[list[str], add]

    # written by `kg_query` (structured Cypher QA answer over Neo4j)
    graph_context: Annotated[list[str], add]

    # written by `combine_results`
    combined_context: Annotated[list[str], add]

    # written by `memory_update`
    memory: Annotated[list[str], add]

    # written by `generate`
    answer: str
