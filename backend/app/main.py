from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore

from backend.app.core.config import FRONTEND_INDEX, get_setting
from backend.app.core.schema import QuestionRequest, AnswerResponse
from backend.app.graph.graph import build_graph


settings = get_setting()

graph = None
store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, store

    async with AsyncPostgresSaver.from_conn_string(settings.DB_URI) as checkpointer, \
               AsyncPostgresStore.from_conn_string(settings.DB_URI) as store:
        
        # Run once against a fresh DB; safe/no-op if tables already exist.
        await checkpointer.setup()
        await store.setup()
 
        builder = build_graph()
        graph = builder.compile(checkpointer=checkpointer, store=store)
        yield
        graph = None


app = FastAPI(
    title="Customer Support Assistant",
    lifespan=lifespan,
)


def sse_event(data: str, event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {data}")
    return "\n".join(lines) + "\n\n"


async def generate_chat_stream(question: str, user_id: str | None = "user-1"):

    user_id = user_id or "user-1"
    config = {
        "configurable": {
            "thread_id": user_id
        }
    }

    yield sse_event("Thinking...", "status")

    async for message, metadata in graph.astream(
        {"question": question, "thread_id": user_id},
        stream_mode="messages",
        config=config,
    ):
        # only stream tokens from the final answer node,
        # not from the memory-extraction LLM call
        if metadata.get("langgraph_node") != "generate":
            continue

        content = getattr(message, "content", "")

        if isinstance(content, list):
            content = "".join(str(part) for part in content)

        if content:
            yield sse_event(content, "message")

    yield sse_event("done", "done")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with FRONTEND_INDEX.open("r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/chat/stream")
def chat_stream(
    question: str = Query(..., min_length=1),
    user_id: str | None = Query("user-1"),
):
    return StreamingResponse(
        generate_chat_stream(question, user_id=user_id),
        media_type="text/event-stream",
    )


@app.post("/chat", response_model=AnswerResponse)
async def chat(request: QuestionRequest):
    user_id = request.user_id or "user-1"
    config = {
        "configurable": {
            "thread_id": user_id
        }
    }
 
    result = await graph.ainvoke(
        {"question": request.question, "thread_id": user_id},
        config=config,
    )
    return AnswerResponse(
        answer=result.get("answer", "I couldn't generate an answer for that question."))


@app.get("/memory/{thread_id}")
async def get_memory(thread_id: str):
    namespace = ("memory", thread_id)
    item = await store.aget(namespace, "facts")
 
    if item is None:
        return {"thread_id": thread_id, "facts": []}
 
    return {"thread_id": thread_id, "facts": item.value.get("facts", [])}


@app.delete("/memory/{thread_id}")
async def delete_memory(thread_id: str):
    namespace = ("memory", thread_id)
 
    existing = await store.aget(namespace, "facts")
    if existing is None:
        raise HTTPException(status_code=404, detail=f"No memory found for thread_id={thread_id}")
 
    await store.adelete(namespace, "facts")
    return {"message": f"Memory deleted for thread_id={thread_id}"}
