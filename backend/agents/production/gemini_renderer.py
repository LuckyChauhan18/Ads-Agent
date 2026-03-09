"""Backward-compatible re-export of GeminiRenderer.

The actual implementation has been modularized into:
    agents/production/render/
        ├── renderer.py       — Main GeminiRenderer class (init, render_variant, generate_output)
        ├── asset_loader.py   — GridFS asset loading, Veo reference images
        ├── prompt_builder.py — LLM scene prompts, per-scene Veo prompt building
        ├── video_merger.py   — FFmpeg: normalize, fast merge, download
        └── overlay.py        — Branding overlays, fallback image videos

Usage (unchanged):
    from agents.production.gemini_renderer import GeminiRenderer
"""
from agents.production.render import GeminiRenderer

__all__ = ["GeminiRenderer"]
