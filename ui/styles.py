"""UI styles — delegated to ``src.styles`` for theming."""

from __future__ import annotations

from src.styles.theme import apply_theme_styles


def apply_styles(theme: str | None = None) -> None:
    apply_theme_styles(theme)


__all__ = ["apply_styles"]
