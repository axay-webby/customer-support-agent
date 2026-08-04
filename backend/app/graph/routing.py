import re


KG_QUERY_KEYWORDS = [
    "relationship",
    "connected",
    "connected to",
    "related",
    "depends on",
    "dependency",
    "graph",
    "node",
    "customer journey",
    "linked",
    "associate",
    "associated",
    "who is",
    "which customers",
    "which user",
    "which accounts",
    "between",
]


def should_use_kg_query(question: str) -> bool:
    if not question:
        return False

    normalized = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
    if not normalized:
        return False

    return any(keyword in normalized for keyword in KG_QUERY_KEYWORDS)
