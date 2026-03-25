"""
AI Chat Router
Agentic RAG chatbot endpoint (placeholder for Phase 6)
"""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser
from app.schemas.ai import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest, user: CurrentUser):
    """
    Ask a natural language question about cricket data.
    Routes to Text-to-SQL or Vector Search via LangGraph agent.

    TODO: Integrate LangGraph agent (Phase 6)
    """
    # Placeholder response until Phase 6
    return ChatResponse(
        answer=(
            f"AI chat is coming soon! Your question: '{request.query}' will be "
            "answered by our agentic RAG pipeline using Text-to-SQL and vector search. "
            "This feature will be available in a future update."
        ),
        tool_used="none",
        sources=[],
        confidence=0.0,
    )
