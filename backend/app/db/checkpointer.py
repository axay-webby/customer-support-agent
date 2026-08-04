from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore

from backend.app.core.config import get_setting
from backend.app.graph.graph import build_graph

settings = get_setting()


@asynccontextmanager
async def compiled_graph():

    builder = build_graph()

    async with AsyncPostgresSaver.from_conn_string(settings.DB_URI) as checkpointer, \
               AsyncPostgresStore.from_conn_string(settings.DB_URI) as store:
        
        graph = builder.compile(
            checkpointer=checkpointer, 
            store=store
        )

        yield graph
