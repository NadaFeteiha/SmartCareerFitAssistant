import re


def unwrap_llm_json(text: str) -> str:
    """Strip markdown code fences and leading/trailing whitespace from LLM output."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text
