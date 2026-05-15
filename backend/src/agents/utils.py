import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def unwrap_llm_json(text: str) -> str:
    """Strip markdown code fences and surrounding whitespace from LLM output."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    return match.group(1).strip() if match else text


def _repair_truncated_json(text: str) -> str:
    """Best-effort repair for LLM JSON truncated by max_tokens.

    Closes unbalanced strings, objects, and arrays so the result parses.
    String-aware: ignores brackets inside string literals. Also strips trailing
    commas immediately before any appended closers.
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


def parse_model(raw: str, model_cls: type[T]) -> T:
    """Parse LLM text output into a Pydantic model.

    Steps:
        1. Strip ```json ... ``` code fences.
        2. Close any unbalanced brackets/strings (truncation by max_tokens).
        3. Drop trailing commas — small models love them.
        4. Validate. Model-level validators on the target class coerce common
        small-model quirks (bare strings instead of objects, None instead of [],
        etc.) without needing per-call sanitization functions.
    """
    text = unwrap_llm_json(raw)
    text = re.sub(r",\s*([\]}])", r"\1", text)
    text = _repair_truncated_json(text)
    return model_cls.model_validate_json(text)
