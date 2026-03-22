"""
Shared utilities for all agents.

llama3.2 wraps every structured output in a tool-call envelope:
  {"name": "...", "parameters": { ...actual data... }}

unwrap_llm_json() strips that wrapper and repairs common JSON issues
before Pydantic validation.
"""
import re
import json


def _repair_json(text: str) -> str:
    """
    Fix the most common JSON mistakes llama3.2 produces:
        1. Trailing commas before } or ]
        2. Single-quoted strings instead of double-quoted
        3. Unquoted keys
    """
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Replace single-quoted strings with double-quoted
    # Only replace when the single quote is used as a string delimiter
    text = re.sub(r"(?<![\\])'([^']*)'", r'"\1"', text)

    # JSON should use true/false/null, but LLMs sometimes output Python literals
    text = re.sub(r"\bNone\b", "null", text)
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)

    # Remove JavaScript-style comments (// and /* */)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    return text


def unwrap_llm_json(raw: str) -> str:
    """
    Strip tool-call wrappers, markdown fences, and repair common
    JSON issues from LLM output before passing to Pydantic.

    Handles these llama3.2 patterns:
        - {"name": "...", "parameters": {...}}   → returns inner dict
        - {"name": "...", "parameters": "..."}   → parses inner string
        - ```json\\n{...}\\n```                   → strips fences
        - Trailing commas, single quotes         → repaired automatically
        - Plain JSON                             → returned as-is
    """
    # Step 1: strip markdown fences
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()

    # Step 1b: remove control characters that make JSON invalid
    # Keep \t (0x09), \n (0x0A), \r (0x0D) — strip everything else in 0x00-0x1F
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean)

    # Step 2: try to parse as-is first to avoid corrupting valid JSON
    # (e.g. _repair_json's single-quote regex mangles apostrophes in strings)
    def _try_parse(text: str):
        try:
            return json.loads(text), True
        except json.JSONDecodeError:
            return None, False

    parsed, ok = _try_parse(clean)
    if not ok:
        # Step 2b: repair common JSON issues and retry
        repaired = _repair_json(clean)
        parsed, ok = _try_parse(repaired)
        if not ok:
            # Step 2c: Try to fix truncation by appending logical closing characters
            for suffix in ['"}', '}', '"]}', ']}']:
                parsed, ok = _try_parse(repaired + suffix)
                if ok:
                    break
            if not ok:
                # Last resort: extract the first {...} block and repair
                match = re.search(r"\{.*\}", clean, re.DOTALL)
                if match:
                    # Could still be malformed or need the suffix trick
                    extracted = match.group(0)
                    for suffix in ["", '"}', '}', '"]}', ']}']:
                        inner_parsed, inner_ok = _try_parse(_repair_json(extracted) + suffix)
                        if inner_ok:
                            return json.dumps(inner_parsed)
                    return _repair_json(extracted)
                # If everything failed, just try appending suffixes to the raw clean string
                for suffix in ['"}', '}', '"]}', ']}']:
                    last_parsed, last_ok = _try_parse(clean + suffix)
                    if last_ok:
                        return json.dumps(last_parsed)
                return clean

    # Step 3: unwrap tool-call envelope if present
    if isinstance(parsed, dict) and "parameters" in parsed:
        inner = parsed["parameters"]
        if isinstance(inner, str):
            inner_parsed, ok2 = _try_parse(inner)
            if not ok2:
                inner_parsed, _ = _try_parse(_repair_json(inner))
            if inner_parsed is not None:
                inner = inner_parsed
        parsed = inner

    # Step 4: coerce empty strings to empty lists for known list fields
    if isinstance(parsed, dict):
        list_fields = {
            "skills", "experiences", "education",
            "required_skills", "responsibilities", "keywords",
            "strengths", "missing_hard_skills", "missing_soft_skills",
            "learning_roadmap", "highlights",
        }
        for field in list_fields:
            if field in parsed and parsed[field] == "":
                parsed[field] = []

    return json.dumps(parsed)