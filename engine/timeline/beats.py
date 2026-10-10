import re
from typing import Any, Dict, List, Optional

MIN_SCENE_DURATION = 0.3  # Minimum duration in seconds to prevent zero-duration collapse


def _clean_word(word: str) -> str:
    """Strip punctuation and lowercase for reliable alignment matching."""
    if not word:
        return ""
    # Strip non-alphanumeric leading/trailing characters
    return re.sub(r"^[^\w]+|[^\w]+$", "", word).lower()


def align_timeline(
    scenes: List[Dict[str, Any]], words: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Maps AI scene start words and emphasis words to Whisper timestamps.

    Guarantees:
    - Strictly monotonic scene start times (scene[i].start_time > scene[i-1].start_time).
    - Prevents zero-duration collapse even with word mismatches or transcription skips.
    - Guarantees emphasis_time >= scene start_time.
    - Preserves all visual attributes on scene dicts.
    """
    word_idx = 0
    last_start_time = 0.0
    timed_scenes: List[Dict[str, Any]] = []

    for scene in scenes:
        spoken_text = scene.get("spoken_text", "")
        if not spoken_text:
            continue

        words_in_text = spoken_text.split()
        if not words_in_text:
            continue

        seg_first_word = _clean_word(words_in_text[0])
        scene_word_count = len(words_in_text)

        matched = False
        candidate_start = 0.0
        match_idx = word_idx

        if words:
            # Search forward from current word cursor
            for temp_idx in range(word_idx, len(words)):
                cleaned_whisper_word = _clean_word(words[temp_idx].get("word", ""))
                if cleaned_whisper_word and cleaned_whisper_word == seg_first_word:
                    candidate_start = float(words[temp_idx].get("start", 0.0))
                    matched = True
                    match_idx = temp_idx
                    # Advance cursor past this matched token for future scenes
                    word_idx = temp_idx + 1
                    break

            if not matched:
                # Word mismatch fallback: estimate position using cursor in words
                if word_idx < len(words):
                    candidate_start = float(words[word_idx].get("start", 0.0))
                elif timed_scenes:
                    candidate_start = last_start_time + MIN_SCENE_DURATION
                else:
                    candidate_start = 0.0
                match_idx = word_idx
                # Advance cursor past this scene's word count so subsequent scenes search forward
                word_idx = min(word_idx + scene_word_count, len(words))
        else:
            # Fallback if words list is empty
            candidate_start = last_start_time + MIN_SCENE_DURATION if timed_scenes else 0.0

        # Enforce strict monotonicity and minimum scene duration to prevent zero-duration collapse
        if timed_scenes:
            scene_start_time = max(candidate_start, last_start_time + MIN_SCENE_DURATION)
        else:
            scene_start_time = max(0.0, candidate_start)

        scene_start_time = round(scene_start_time, 3)
        last_start_time = scene_start_time

        # Search for emphasis timestamp
        emphasis_word = _clean_word(scene.get("emphasis_word", ""))
        emphasis_time = scene_start_time

        if emphasis_word and words:
            search_start = max(0, match_idx)
            search_end = min(len(words), match_idx + scene_word_count + 5)
            for s_idx in range(search_start, search_end):
                cleaned_w = _clean_word(words[s_idx].get("word", ""))
                if cleaned_w and cleaned_w == emphasis_word:
                    emp_cand = float(words[s_idx].get("start", 0.0))
                    if emp_cand >= scene_start_time:
                        emphasis_time = round(emp_cand, 3)
                    break

        if emphasis_time < scene_start_time:
            emphasis_time = scene_start_time

        timed_scene: Dict[str, Any] = {
            "scene_type": scene.get("scene_type", "code_reveal"),
            "spoken_text": spoken_text,
            "start_time": scene_start_time,
            "emphasis_time": emphasis_time,
        }

        # Carry over all visual and content properties
        for key in [
            "display_text",
            "code_snippet",
            "nodes",
            "problem_label",
            "problem_code",
            "solution_label",
            "solution_code",
            "focus_phrase",
            "target_code",
            "title",
            "emphasis_word",
        ]:
            if key in scene and key not in timed_scene:
                timed_scene[key] = scene[key]

        timed_scenes.append(timed_scene)

    return timed_scenes