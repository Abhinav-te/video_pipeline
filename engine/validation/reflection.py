"""
engine/validation/reflection.py

Unified Self-Correcting Reflection Loop (Stage 2 -> Stage 4.8 -> Stage 6):
Serializes structural and rendering errors into <run_dir>/reflection.error.json
and provides automated deterministic healing for timing, monotonic bounds,
and schema invariants.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def write_reflection_error(
    run_dir: Path,
    stage: str,
    message: str,
    errors: Optional[List[str]] = None,
    scene_id: Optional[int] = None,
    field_path: Optional[str] = None,
) -> Path:
    """
    Serializes a structured error object into <run_dir>/reflection.error.json
    for auto-healing and diagnostic inspection.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    error_payload = {
        "stage": stage,
        "message": message,
        "errors": errors or [message],
        "scene_id": scene_id,
        "field_path": field_path,
        "timestamp": time.time(),
        "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    error_file = run_dir / "reflection.error.json"
    with open(error_file, "w", encoding="utf-8") as f:
        json.dump(error_payload, f, indent=2)
        
    print(f"[REFLECTION:RECORD] 📝 Failure recorded in {error_file.name} (Stage: {stage})", flush=True)
    return error_file


def read_reflection_error(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Reads the last reflection error if present."""
    error_file = Path(run_dir) / "reflection.error.json"
    if error_file.exists():
        try:
            with open(error_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def clear_reflection_error(run_dir: Path) -> None:
    """Removes any stale reflection error from a previous attempt."""
    error_file = Path(run_dir) / "reflection.error.json"
    if error_file.exists():
        try:
            error_file.unlink()
        except Exception:
            pass


def auto_heal_timeline_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """
    Auto-heals deterministic scene timing and schema fields:
      - Enforces non-negative start_time (>= 0.0)
      - Guarantees strict monotonicity: start_time < end_time
      - Enforces minimum scene duration (>= 2.5s)
      - Fixes Whisper words with end <= start or non-chronological order
      - Fills missing visual_type / title / spoken_text fallbacks
    Returns (healed_payload, was_modified).
    """
    modified = False
    
    # 1. Words Monotonicity Check & Healing
    words = payload.get("words", [])
    if isinstance(words, list) and words:
        prev_start = 0.0
        for w in words:
            if not isinstance(w, dict):
                continue
            s = float(w.get("start", 0.0))
            e = float(w.get("end", s + 0.1))
            
            if s < 0.0:
                w["start"] = 0.0
                s = 0.0
                modified = True
                
            if s < prev_start:
                w["start"] = round(prev_start, 3)
                s = prev_start
                modified = True
                
            if e <= s:
                w["end"] = round(s + 0.15, 3)
                modified = True
                
            prev_start = float(w.get("start", 0.0))

    # 2. Scenes Monotonicity & Invariants
    scenes = payload.get("scenes", [])
    if isinstance(scenes, list) and scenes:
        prev_scene_start = 0.0
        for idx, sc in enumerate(scenes):
            if not isinstance(sc, dict):
                continue
                
            # Default ID & Title
            if "scene_id" not in sc:
                sc["scene_id"] = idx
                modified = True
            if not sc.get("title"):
                display_txt = sc.get("display_text") or ""
                spoken_txt = sc.get("spoken_text") or sc.get("narration") or ""
                if display_txt:
                    sc["title"] = display_txt.title()
                elif spoken_txt:
                    words = [w for w in spoken_txt.split() if len(w) > 3][:4]
                    sc["title"] = " ".join(words).title() if words else f"Core Insight {idx + 1}"
                else:
                    sc["title"] = f"Core Principle {idx + 1}"
                modified = True
            if not sc.get("visual_type"):
                sc["visual_type"] = "fullscreen_text" if idx == 0 else "concept"
                modified = True
                
            s = float(sc.get("start_time", 0.0))
            e = float(sc.get("end_time", s + 2.5))
            
            if idx == 0 and s != 0.0:
                sc["start_time"] = 0.0
                s = 0.0
                modified = True
                
            if s < prev_scene_start:
                sc["start_time"] = round(prev_scene_start, 3)
                s = prev_scene_start
                modified = True
                
            if e < s + 2.5:
                sc["end_time"] = round(s + 2.5, 3)
                e = sc["end_time"]
                modified = True
                
            prev_scene_start = float(sc.get("start_time", 0.0))

            # Strip null/None values so Zod schema validation passes cleanly
            null_keys = [k for k, v in list(sc.items()) if v is None]
            for k in null_keys:
                del sc[k]
                modified = True
    return payload, modified

