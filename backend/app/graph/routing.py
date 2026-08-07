import re


def should_use_kg_query(question: str) -> bool:
    text = (question or "").strip().lower()
    if not text:
        return False

    relationship_keywords = [
        "connected",
        "connection",
        "linked",
        "relationship",
        "related",
        "depend",
        "dependency",
        "customer journey",
        "journey",
        "customer",
        "customers",
    ]

    return any(keyword in text for keyword in relationship_keywords)
