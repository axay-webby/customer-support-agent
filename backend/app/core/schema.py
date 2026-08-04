from typing import Annotated, List
from pydantic import BaseModel, Field, EmailStr


""" response validation """
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    user_id: str | None = Field(
        None, description="Optional user identifier for personal memory"
    )

class AnswerResponse(BaseModel):
    answer: str


""" memory validation """
class MemoryItem(BaseModel):
    text: Annotated[str, Field(description="Atomic user memory")]
    is_new: Annotated[bool, Field(description="True if new, false if duplicate")]
 
 
class MemoryDecision(BaseModel):
    should_write: bool
    memories: Annotated[List[MemoryItem], Field(default_factory=list)]
