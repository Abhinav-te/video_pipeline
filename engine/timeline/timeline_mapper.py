"""
engine/timeline/timeline_mapper.py

Deterministic Timeline Mapper & Subtitle Chunker.
- Maps scenes to exact cumulative audio offsets based on measured WAV durations (no max(2.5, duration) clamping).
- Resolves emphasis_time and workflow state machine events (at_word / timestamp_sec) from display-mapped words.
- Generates caption_chunks with hard splits on sentence punctuation (. ! ? ; :) and soft splits on commas or <= 28 chars.
- Replaces legacy 2,344-line choreographer.py.
"""

import copy
import re
from typing import Any, Dict, List, Optional, Tuple, Union


# Domain theme palettes for consistent B2B branding
THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "code": {
        "primary": "#38bdf8",
        "secondary": "#818cf8",
        "accent": "#34d399",
        "bg_card": "rgba(15, 23, 42, 0.75)",
        "border": "rgba(56, 189, 248, 0.25)",
        "text": "#f8fafc",
    },
    "devtools": {
        "primary": "#6366f1",
        "secondary": "#a855f7",
        "accent": "#22c55e",
        "bg_card": "rgba(15, 23, 42, 0.75)",
        "border": "rgba(99, 102, 241, 0.25)",
        "text": "#f8fafc",
    },
    "default": {
        "primary": "#60a5fa",
        "secondary": "#a78bfa",
        "accent": "#4ade80",
        "bg_card": "rgba(15, 23, 42, 0.75)",
        "border": "rgba(96, 165, 250, 0.25)",
        "text": "#f8fafc",
    },
}

COMPARISON_FOOTERS: Dict[str, str] = {
    "code": "KEY TAKEAWAY: Declarative async execution eliminates distributed retry race conditions",
    "devtools": "KEY TAKEAWAY: Isolated step retries prevent duplicate external API side effects",
    "default": "KEY TAKEAWAY: Verifiable developer workflows with zero manual orchestration",
}


def resolve_domain(domain_str: Optional[str]) -> str:
    """Normalizes subject/domain to standard B2B developer category."""
    if not domain_str:
        return "code"
    d = domain_str.strip().lower()
    if d in {"devtools", "api", "sdk", "systems"}:
        return "devtools"
    return "code"


def _clean_token(w: str) -> str:
    """Strips outer punctuation and normalizes token for timestamp matching."""
    if not w:
        return ""
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def chunk_caption_words(
    words: List[Dict[str, Any]],
    max_chars: int = 28,
    max_words: int = 5,
) -> List[Dict[str, Any]]:
    """
    Chunks a list of timed word objects into readable subtitle chunks.
    - Hard splits strictly on sentence boundaries (. ! ?).
    - Soft splits on clause boundaries (, ; :) or when chunk length exceeds max_chars.
    - Guarantees zero cross-sentence bleeding.
    """
    if not words:
        return []

    chunks: List[Dict[str, Any]] = []
    current_words: List[Dict[str, Any]] = []
    current_text = ""

    for w in words:
        word_str = str(w.get("word", "")).strip()
        if not word_str:
            continue

        current_words.append(w)
        current_text += (" " if current_text else "") + word_str

        ends_sentence = bool(re.search(r"[.!?]$", word_str))
        ends_clause = bool(re.search(r"[,;:]$", word_str))
        is_too_long = len(current_words) >= max_words or len(current_text) >= max_chars

        if ends_sentence or (len(current_words) >= 3 and ends_clause) or is_too_long:
            chunks.append({
                "start": round(float(current_words[0].get("start", 0.0)), 3),
                "end": round(float(current_words[-1].get("end", 0.0)), 3),
                "text": current_text,
                "words": list(current_words),
            })
            current_words = []
            current_text = ""

    if current_words:
        chunks.append({
            "start": round(float(current_words[0].get("start", 0.0)), 3),
            "end": round(float(current_words[-1].get("end", 0.0)), 3),
            "text": current_text,
            "words": list(current_words),
        })

    return chunks


def resolve_word_timestamp(
    words: List[Dict[str, Any]],
    target_phrase: str,
    default_time: float,
    start_search_idx: int = 0,
) -> Tuple[float, int]:
    """
    Finds the start timestamp for target_phrase in words list.
    Returns (resolved_timestamp_sec, matched_word_idx).
    """
    if not words or not target_phrase:
        return default_time, start_search_idx

    target_clean = _clean_token(target_phrase)
    for idx in range(start_search_idx, len(words)):
        w_clean = _clean_token(str(words[idx].get("word", "")))
        if w_clean and (w_clean == target_clean or target_clean in w_clean):
            return round(float(words[idx].get("start", default_time)), 3), idx

    return default_time, start_search_idx


def map_scene_timeline(
    scenes: List[Dict[str, Any]],
    scene_audio_results: List[Dict[str, Any]],
    domain: str = "code",
    fps: int = 30,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Maps scenes to exact cumulative audio offsets derived from measured WAV lengths.
    Resolves emphasis_time, event activation timings, and subtitle caption_chunks.

    scene_audio_results: list of dicts with:
      - scene_id: int
      - duration: float (exact measured WAV duration)
      - words: list of word dicts relative to 0.0s of that scene

    Returns (timed_scenes, master_words, master_caption_chunks).
    """
    if not scenes:
        return [], [], []

    audio_by_id = {item.get("scene_id"): item for item in scene_audio_results}

    current_time = 0.0
    master_words: List[Dict[str, Any]] = []
    timed_scenes: List[Dict[str, Any]] = []

    active_domain = resolve_domain(domain)
    palette = THEME_PALETTES.get(active_domain, THEME_PALETTES["default"])

    for idx, raw_scene in enumerate(scenes):
        scene = copy.deepcopy(raw_scene)
        scene_id = scene.get("scene_id", idx + 1)

        # Lookup audio result for this scene
        audio_meta = audio_by_id.get(scene_id) or (scene_audio_results[idx] if idx < len(scene_audio_results) else {})
        dur = float(audio_meta.get("duration", scene.get("duration", 3.0)))

        start_time = round(current_time, 3)
        end_time = round(start_time + dur, 3)

        # Map relative word timestamps to global video timeline
        scene_words: List[Dict[str, Any]] = []
        raw_words = audio_meta.get("words", [])
        for w in raw_words:
            w_start = round(start_time + float(w.get("start", 0.0)), 3)
            w_end = round(start_time + float(w.get("end", 0.0)), 3)
            w_item = {
                "word": w.get("word", ""),
                "start": w_start,
                "end": max(w_start + 0.05, w_end),
            }
            scene_words.append(w_item)
            master_words.append(w_item)

        # Resolve emphasis_time
        emp_word = scene.get("emphasis_word")
        if emp_word and scene_words:
            emp_time, _ = resolve_word_timestamp(scene_words, emp_word, start_time)
            scene["emphasis_time"] = emp_time
        else:
            scene["emphasis_time"] = start_time

        # Resolve workflow event timestamps (at_word -> timestamp_sec)
        visual = scene.get("visual") or {}
        events = visual.get("events") or scene.get("events") or []
        if events and scene_words:
            search_idx = 0
            num_events = len(events)
            for e_idx, ev in enumerate(events):
                at_word = ev.get("at_word")
                if at_word:
                    t_sec, next_search = resolve_word_timestamp(
                        scene_words, at_word, start_time + (e_idx + 1) * (dur / (num_events + 1)), search_idx
                    )
                    ev["timestamp_sec"] = t_sec
                    search_idx = next_search + 1
                elif "timestamp_sec" not in ev:
                    # Distribute evenly if no at_word specified
                    ev["timestamp_sec"] = round(start_time + (e_idx + 1) * (dur / (num_events + 1)), 3)

        # Generate scene-level subtitle caption chunks
        scene["caption_chunks"] = chunk_caption_words(scene_words)

        # Attach standard timeline & theme metadata
        scene["start_time"] = start_time
        scene["end_time"] = end_time
        scene["duration"] = dur
        scene["theme"] = palette
        scene["domain"] = active_domain

        timed_scenes.append(scene)
        current_time = end_time

    # Generate master global caption chunks
    master_caption_chunks = chunk_caption_words(master_words)

    return timed_scenes, master_words, master_caption_chunks


def choreograph_scenes(
    scenes: List[Dict[str, Any]],
    words: List[Dict[str, Any]],
    domain: str = "code",
    fps: int = 30,
) -> List[Dict[str, Any]]:
    """
    Backward-compatibility shim for legacy callers of choreographer.choreograph_scenes.
    Delegates to timeline_mapper logic with zero bloat.
    """
    if not scenes:
        return []

    # If scenes already have duration from WAV synthesis
    scene_audio_results = []
    for s in scenes:
        s_id = s.get("scene_id", 1)
        st = float(s.get("start_time", 0.0))
        et = float(s.get("end_time", st + float(s.get("duration", 3.0))))
        dur = max(0.1, et - st)
        s_words = [
            {"word": w.get("word", ""), "start": round(float(w.get("start", 0.0)) - st, 3), "end": round(float(w.get("end", 0.0)) - st, 3)}
            for w in words
            if st <= float(w.get("start", 0.0)) < et
        ]
        scene_audio_results.append({
            "scene_id": s_id,
            "duration": dur,
            "audio_path": s.get("audio_file", ""),
            "words": s_words,
        })

    timed_scenes, _, _ = map_scene_timeline(scenes, scene_audio_results, domain=domain, fps=fps)
    return timed_scenes
