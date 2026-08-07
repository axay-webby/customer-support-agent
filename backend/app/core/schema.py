from typing import Annotated, List
from pydantic import BaseModel, Field


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


""" Allowed Schema for Knowledge Graph """
ALLOWED_NODES = [
    "Company",
    "Product",
    "Customer",
    "BusinessCustomer",
    "Order",
    "Shipping",
    "Tracking",
    "Payment",
    "Refund",
    "Return",
    "Warranty",
    "Support",
    "Account",
    "Invoice",
    "Location",
    "Technology",
]

ALLOWED_RELATIONSHIPS = [
    "SELLS",
    "OPERATES_IN",
    "SHIPS_TO",
    "HAS_INFORMATION",
    "CAN_COMPARE",
    "CAN_REQUEST",
    "PLACES",
    "USES",
    "GENERATES",
    "SENT_VIA",
    "CAN_UPDATE",
    "REQUIRES",
    "PROCESSED_AFTER",
    "HAS_WARRANTY",
    "SUPPORTS_PAYMENT",
    "HAS_FEATURE",
    "AVAILABLE_VIA",
    "RESPONDS_WITHIN",
    "REPORTED_WITHIN",
]