from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_experimental.graph_transformers import LLMGraphTransformer

from backend.app.core.config import get_setting
from backend.app.service.llms import get_llm
from backend.app.service.vector_store import load_document, split_documents, should_refresh_pdf_assets

settings = get_setting()


def get_graph_db():

    return Neo4jGraph(
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE,
    )


def _graph_has_data(graph_db: Neo4jGraph) -> bool:

    result = graph_db.query("MATCH (n) RETURN count(n) AS count")
    return bool(result) and result[0]["count"] > 0


def ingest_pdf_to_graph(pdf_path: str, graph_db: Neo4jGraph | None = None, force_refresh: bool = False):

    graph_db = graph_db or get_graph_db()

    should_refresh = force_refresh or should_refresh_pdf_assets(pdf_path)

    if should_refresh:
        graph_db.query("MATCH (n) DETACH DELETE n")
    elif _graph_has_data(graph_db):
        return

    documents = load_document(pdf_path)
    chunks = split_documents(documents)

    llm = get_llm()
    transformer = LLMGraphTransformer(llm=llm)
    graph_documents = transformer.convert_to_graph_documents(chunks)

    graph_db.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True,
    )


def create_cypher_chain():

    graph_db = get_graph_db()
    llm = get_llm()

    return GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph_db,
        verbose=True,
        allow_dangerous_requests=True,
        return_direct=False,
    )
