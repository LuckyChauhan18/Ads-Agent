"""Render package — modular GeminiRenderer.

Re-exports GeminiRenderer for clean imports:
    from agents.production.render import GeminiRenderer
"""
from .renderer import GeminiRenderer

__all__ = ["GeminiRenderer"]
