from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, List, TypedDict

from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

import retriever


class GraphState(TypedDict):
    # add_messages reducer is what lets LangGraph merge streaming message chunks
    # into a coherent assistant reply while persisting state across turns.
    messages: Annotated[List[BaseMessage], add_messages]
    video_metadata: Dict[str, Any]
    session_id: str
    context: str


SYSTEM_PROMPT = """
You are a social media analytics expert helping video creators understand
their content performance.

You have access to transcripts and metadata for two videos:

VIDEO A:
- Title: {video_a_title}
- Creator: {video_a_creator}
- Views: {video_a_views}
- Likes: {video_a_likes}
- Comments: {video_a_comments}
- Engagement Rate: {video_a_engagement_rate}%
- Follower Count: {video_a_follower_count}
- Upload Date: {video_a_upload_date}
- Duration: {video_a_duration}s
- Hashtags: {video_a_hashtags}

VIDEO B:
- Title: {video_b_title}
- Creator: {video_b_creator}
- Views: {video_b_views}
- Likes: {video_b_likes}
- Comments: {video_b_comments}
- Engagement Rate: {video_b_engagement_rate}%
- Follower Count: {video_b_follower_count}
- Upload Date: {video_b_upload_date}
- Duration: {video_b_duration}s
- Hashtags: {video_b_hashtags}

RETRIEVED CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

RULES:
1. Always cite your sources: [Video A | Chunk N] or [Video B | Chunk N]
2. Never make up data. If something isn't in the context, say so.
3. When comparing engagement, always show the exact numbers and rates.
4. When asked about hooks, refer specifically to the earliest chunks.
5. Keep responses concise but analytical.
6. Suggest improvements based only on what actually worked in the higher-performing video.
""".strip()


def _format_history(messages: List[BaseMessage]) -> str:
    lines: List[str] = []
    for m in messages:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        content = getattr(m, "content", "")
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _safe_get(video_meta: Dict[str, Any], key: str, default: Any = None) -> Any:
    v = video_meta.get(key, default)
    return default if v is None else v


def retrieve_node(state: GraphState) -> Dict[str, Any]:
    last_user = state["messages"][-1]
    query = getattr(last_user, "content", "") or ""

    chunks = retriever.retrieve(query=query, video_ids=["A", "B"], n_results=6)

    context_lines: List[str] = []
    for ch in chunks:
        md = ch.get("metadata") or {}
        vid = md.get("video_id", "?")
        idx = md.get("chunk_index", "?")
        content = (ch.get("content") or "").strip()
        if content:
            context_lines.append(f"[Video {vid} | Chunk {idx}]: {content}")

    return {"context": "\n".join(context_lines).strip()}


async def llm_node(state: GraphState):
    """
    We stream from the model directly so the UI can render tokens immediately.
    The add_messages reducer will stitch chunks into a single assistant message
    for durable session memory.
    """
    video_a = state["video_metadata"].get("video_a", {})
    video_b = state["video_metadata"].get("video_b", {})

    prompt = SYSTEM_PROMPT.format(
        video_a_title=_safe_get(video_a, "title", "Untitled"),
        video_a_creator=_safe_get(video_a, "creator", "Unknown"),
        video_a_views=_safe_get(video_a, "views", 0),
        video_a_likes=_safe_get(video_a, "likes", 0),
        video_a_comments=_safe_get(video_a, "comments", 0),
        video_a_engagement_rate=_safe_get(video_a, "engagement_rate", 0.0),
        video_a_follower_count=_safe_get(video_a, "follower_count", None),
        video_a_upload_date=_safe_get(video_a, "upload_date", None),
        video_a_duration=_safe_get(video_a, "duration", None),
        video_a_hashtags=_safe_get(video_a, "hashtags", []),
        video_b_title=_safe_get(video_b, "title", "Untitled"),
        video_b_creator=_safe_get(video_b, "creator", "Unknown"),
        video_b_views=_safe_get(video_b, "views", 0),
        video_b_likes=_safe_get(video_b, "likes", 0),
        video_b_comments=_safe_get(video_b, "comments", 0),
        video_b_engagement_rate=_safe_get(video_b, "engagement_rate", 0.0),
        video_b_follower_count=_safe_get(video_b, "follower_count", None),
        video_b_upload_date=_safe_get(video_b, "upload_date", None),
        video_b_duration=_safe_get(video_b, "duration", None),
        video_b_hashtags=_safe_get(video_b, "hashtags", []),
        context=state.get("context", ""),
        history=_format_history(state.get("messages", [])),
    )

    model_name = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

    llm = ChatOpenAI(model=model_name, streaming=True, temperature=temperature)

    query = getattr(state["messages"][-1], "content", "") or ""
    messages = [SystemMessage(content=prompt), HumanMessage(content=query)]

    async for chunk in llm.astream(messages):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield {"messages": [chunk]}


def _build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("llm_node", llm_node)
    graph.add_edge(START, "retrieve_node")
    graph.add_edge("retrieve_node", "llm_node")
    graph.add_edge("llm_node", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


_APP = _build_graph()


async def run_graph_streaming(
    query: str, session_id: str, video_metadata: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Runs the LangGraph graph and yields model tokens as they stream.
    """
    if not query.strip():
        return

    inputs: Dict[str, Any] = {
        "messages": [HumanMessage(content=query)],
        "video_metadata": video_metadata,
        "session_id": session_id,
        "context": "",
    }

    config = {"configurable": {"thread_id": session_id}}

    async for item in _APP.astream(inputs, config=config, stream_mode="messages"):
        # LangGraph yields either a BaseMessage or (node_name, BaseMessage) depending on version.
        msg = item[1] if isinstance(item, tuple) and len(item) == 2 else item
        if isinstance(msg, AIMessageChunk):
            token = msg.content or ""
            if token:
                yield token


# Commit message suggestion:
#   "Add LangGraph RAG graph with streaming GPT-4o-mini and MemorySaver sessions"
