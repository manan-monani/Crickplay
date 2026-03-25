"""
AI Chat Pydantic Schemas
Request/response models for the Agentic RAG chatbot
"""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """AI chat query request."""
    query: str = Field(..., max_length=2000, description="Natural language question")
    conversation_id: Optional[str] = Field(
        None,
        description="Session ID for follow-up questions"
    )


class ChatResponse(BaseModel):
    """AI chat response with tool attribution."""
    answer: str
    tool_used: str = Field(
        description="Which tool was used: text_to_sql, vector_search, or both"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source references for the answer"
    )
    sql_query: Optional[str] = Field(
        None,
        description="Generated SQL query (if text_to_sql was used)"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Model confidence in the answer"
    )


class NarrativeResponse(BaseModel):
    """Auto-generated match narrative."""
    match_id: str
    over_number: int
    persona: str = Field(description="Target audience: coach, bettor, broadcaster")
    narrative: str
    win_probability_delta: float
    generated_at: str
