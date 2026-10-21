"""
engine/timeline/__init__.py

Timeline Mapping, Subtitle Chunking & Audio Synchronization.
"""

from .timeline_mapper import (
    map_scene_timeline,
    chunk_caption_words,
    resolve_word_timestamp,
    choreograph_scenes,
    THEME_PALETTES,
    COMPARISON_FOOTERS,
    resolve_domain,
)

__all__ = [
    "map_scene_timeline",
    "chunk_caption_words",
    "resolve_word_timestamp",
    "choreograph_scenes",
    "THEME_PALETTES",
    "COMPARISON_FOOTERS",
    "resolve_domain",
]
