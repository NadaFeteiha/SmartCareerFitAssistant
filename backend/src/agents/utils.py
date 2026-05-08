import re


def unwrap_llm_json(text: str) -> str:
    """Strip markdown code fences and leading/trailing whitespace from LLM output."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


def repair_truncated_json(text: str) -> str:
    """Best-effort repair for LLM JSON truncated by a max_tokens cap.

    Closes any unbalanced strings, objects, and arrays so the result parses.
    String-aware: does not count braces that occur inside string literals.
    Also strips trailing commas immediately before the appended closers.
    """
    if not text:
        return text

    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack and ((stack[-1] == "{" and ch == "}") or (stack[-1] == "[" and ch == "]")):
                stack.pop()

    repaired = text
    if in_string:
        repaired += '"'
    if stack:
        repaired = re.sub(r",\s*$", "", repaired)
        for opener in reversed(stack):
            repaired += "}" if opener == "{" else "]"
    return repaired
