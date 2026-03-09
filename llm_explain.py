# llm_explain.py
# Save in: lost_found_reunion/llm_explain.py
#
# WHAT THIS FILE DOES:
# Uses Ollama (llama3.2 running locally) to explain why each
# found item might be the student's lost item.
#
# TOOLS USED: ollama (local LLM — llama3.2)

import ollama


def explain_match(search_query: str, item: dict, confidence: float) -> str:
    """
    Calls local Ollama llama3.2 to generate a friendly explanation
    of why the found item matches the student's query.

    Falls back to a rule-based explanation if Ollama is unavailable.
    """
    prompt = f"""You are a helpful Lost & Found assistant at BLDEACET college.
A student is searching for their lost item. We found a potential match.
Explain in exactly 2 friendly sentences why this found item might be theirs.
Be specific about what matches. Don't repeat the item name unnecessarily.

Student is looking for: "{search_query}"

Found item details:
  Name:        {item['name']}
  Category:    {item['category']}
  Color:       {item.get('color', 'unknown')}
  Description: {item['description'][:150]}
  Confidence:  {confidence:.1f}%

Write only the 2-sentence explanation. Nothing else."""

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 80}
        )
        return response["message"]["content"].strip()

    except Exception:
        return _fallback_explanation(search_query, item, confidence)


def _fallback_explanation(query: str, item: dict, conf: float) -> str:
    """Simple rule-based fallback if Ollama isn't running."""
    query_words = set(query.lower().split())
    name_words  = set(item["name"].lower().split())
    overlap     = query_words & name_words

    if overlap:
        reason = f"both mention '{next(iter(overlap))}'"
    elif item.get("color", "").lower() in query.lower():
        reason = f"the {item['color']} color matches your description"
    else:
        reason = f"it's a {item['category']} item with similar characteristics"

    strength = ("strong" if conf >= 60 else
                "possible" if conf >= 30 else "potential")
    return (f"This is a {strength} match because {reason}. "
            f"Bring item ID {item['item_id']} to the Lost & Found office to verify.")