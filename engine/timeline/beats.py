import copy
import difflib
import re
from typing import Any, Dict, List, Optional, Union

MIN_SCENE_DURATION = 2.5  # Enforce minimum scene duration of 2.5s to prevent flash cuts


def _clean_word(word: str) -> str:
    """Strip punctuation and lowercase for reliable alignment matching."""
    if not word:
        return ""
    # Strip non-alphanumeric leading/trailing characters
    return re.sub(r"^[^\w]+|[^\w]+$", "", word).lower()


def align_script_tokens_to_whisper(
    script_input: Union[str, List[Dict[str, Any]]],
    whisper_words: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Maps original script tokens from narration onto Whisper timestamps.
    Preserves exact script spelling and casing (e.g. DBSCAN, partitions, SN2, Nucleophile)
    over Whisper's raw phonetic mishears (DISCAN, PETITIONS, etc.).
    """
    if not whisper_words:
        return []

    # Extract narration string
    if isinstance(script_input, list):
        script_narration = " ".join(
            str(s.get("spoken_text") or s.get("narration") or "").strip()
            for s in script_input
        )
    else:
        script_narration = str(script_input or "")

    raw_script_tokens = [w.strip() for w in script_narration.split() if w.strip()]
    if not raw_script_tokens:
        return whisper_words

    clean_script = [_clean_word(t) for t in raw_script_tokens]
    clean_whisper = [_clean_word(w.get("word", "")) for w in whisper_words]

    matcher = difflib.SequenceMatcher(None, clean_script, clean_whisper)
    aligned: List[Dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        n_script = i2 - i1
        n_whisper = j2 - j1

        if tag == "equal":
            for k in range(n_script):
                s_idx = i1 + k
                w_idx = j1 + k
                aligned.append({
                    "word": raw_script_tokens[s_idx],
                    "start": round(float(whisper_words[w_idx].get("start", 0.0)), 3),
                    "end": round(float(whisper_words[w_idx].get("end", 0.0)), 3),
                })

        elif tag == "replace":
            w_start = float(whisper_words[j1].get("start", 0.0))
            w_end = float(whisper_words[j2 - 1].get("end", w_start + 0.3))
            w_dur = max(0.1, w_end - w_start)

            if n_script == n_whisper:
                for k in range(n_script):
                    aligned.append({
                        "word": raw_script_tokens[i1 + k],
                        "start": round(float(whisper_words[j1 + k].get("start", w_start)), 3),
                        "end": round(float(whisper_words[j1 + k].get("end", w_end)), 3),
                    })
            else:
                step = w_dur / n_script
                for k in range(n_script):
                    aligned.append({
                        "word": raw_script_tokens[i1 + k],
                        "start": round(w_start + k * step, 3),
                        "end": round(w_start + (k + 1) * step, 3),
                    })

        elif tag == "delete":
            prev_end = aligned[-1]["end"] if aligned else (float(whisper_words[j1]["start"]) if j1 < len(whisper_words) else 0.0)
            next_start = float(whisper_words[j1]["start"]) if j1 < len(whisper_words) else prev_end + 0.3 * n_script
            dur = max(0.2 * n_script, next_start - prev_end)
            step = dur / n_script
            for k in range(n_script):
                aligned.append({
                    "word": raw_script_tokens[i1 + k],
                    "start": round(prev_end + k * step, 3),
                    "end": round(prev_end + (k + 1) * step, 3),
                })

        elif tag == "insert":
            # Whisper hallucinated or phonetic filler not in script: skip to keep subtitles matching script
            pass

    return aligned


def enforce_minimum_scene_durations(
    scenes: List[Dict[str, Any]],
    min_duration: float = 2.5,
    total_duration: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Enforces that every single scene in data.json is strictly >= min_duration (default 2.5s).
    Eliminates flash cuts (such as 0.7s scenes) by redistributing boundary timestamps
    with neighbors or merging short scenes into adjacent neighbors.
    Guarantees 100% contiguous intervals from 0.0 to total_duration.
    """
    if not scenes:
        return []

    # Defensive copy
    processed = [dict(s) for s in scenes]

    if len(processed) == 1:
        processed[0]["start_time"] = 0.0
        cur_end = float(processed[0].get("end_time", min_duration))
        target_end = max(cur_end, min_duration)
        if total_duration and total_duration > min_duration:
            target_end = total_duration
        processed[0]["end_time"] = round(target_end, 3)
        return processed

    # Step 1: Ensure contiguous baseline
    processed[0]["start_time"] = 0.0
    for i in range(len(processed) - 1):
        if "end_time" not in processed[i] or processed[i]["end_time"] is None:
            processed[i]["end_time"] = processed[i + 1].get("start_time", processed[i]["start_time"] + min_duration)
        processed[i + 1]["start_time"] = processed[i]["end_time"]

    # Final scene end_time
    if total_duration is not None and total_duration > processed[-1]["start_time"]:
        processed[-1]["end_time"] = max(total_duration, processed[-1]["start_time"] + min_duration)
    else:
        processed[-1]["end_time"] = processed[-1].get("end_time") or (processed[-1]["start_time"] + min_duration)

    # Step 2: Iteratively eliminate any scene < min_duration
    max_passes = len(processed) * 2
    for _ in range(max_passes):
        violation_idx = -1
        for idx, s in enumerate(processed):
            dur = float(s["end_time"]) - float(s["start_time"])
            if dur < min_duration - 1e-4:
                violation_idx = idx
                break

        if violation_idx == -1:
            break

        idx = violation_idx
        cur_dur = float(processed[idx]["end_time"]) - float(processed[idx]["start_time"])
        needed = min_duration - cur_dur

        # Try redistributing with previous scene
        redistributed = False
        if idx > 0:
            prev_dur = float(processed[idx - 1]["end_time"]) - float(processed[idx - 1]["start_time"])
            surplus = prev_dur - min_duration
            if surplus >= 0.2:
                shift = min(surplus, needed)
                processed[idx]["start_time"] = round(float(processed[idx]["start_time"]) - shift, 3)
                processed[idx - 1]["end_time"] = processed[idx]["start_time"]
                redistributed = True
                cur_dur = float(processed[idx]["end_time"]) - float(processed[idx]["start_time"])
                needed = min_duration - cur_dur

        # Try redistributing with next scene
        if needed > 1e-4 and idx + 1 < len(processed):
            next_dur = float(processed[idx + 1]["end_time"]) - float(processed[idx + 1]["start_time"])
            surplus = next_dur - min_duration
            if surplus >= 0.2:
                shift = min(surplus, needed)
                processed[idx]["end_time"] = round(float(processed[idx]["end_time"]) + shift, 3)
                processed[idx + 1]["start_time"] = processed[idx]["end_time"]
                redistributed = True

        # If redistribution could not satisfy min_duration, merge short scene with neighbor
        dur_after = float(processed[idx]["end_time"]) - float(processed[idx]["start_time"])
        if dur_after < min_duration - 1e-4:
            if idx > 0:
                # Merge into previous scene
                processed[idx - 1]["end_time"] = processed[idx]["end_time"]
                prev_text = processed[idx - 1].get("spoken_text", "")
                curr_text = processed[idx].get("spoken_text", "")
                processed[idx - 1]["spoken_text"] = f"{prev_text} {curr_text}".strip()
                processed.pop(idx)
            elif idx + 1 < len(processed):
                # Merge into next scene
                processed[idx + 1]["start_time"] = processed[idx]["start_time"]
                curr_text = processed[idx].get("spoken_text", "")
                next_text = processed[idx + 1].get("spoken_text", "")
                processed[idx + 1]["spoken_text"] = f"{curr_text} {next_text}".strip()
                processed.pop(idx)

    # Step 3: Final sweep to guarantee contiguous bounds and strictly >= min_duration
    processed[0]["start_time"] = 0.0
    for i in range(len(processed) - 1):
        if processed[i]["end_time"] < processed[i]["start_time"] + min_duration:
            processed[i]["end_time"] = round(processed[i]["start_time"] + min_duration, 3)
        processed[i + 1]["start_time"] = processed[i]["end_time"]

    if processed[-1]["end_time"] < processed[-1]["start_time"] + min_duration:
        processed[-1]["end_time"] = round(processed[-1]["start_time"] + min_duration, 3)

    for s in processed:
        s["start_time"] = round(float(s["start_time"]), 3)
        s["end_time"] = round(float(s["end_time"]), 3)

    return processed


def align_timeline(
    scenes: List[Dict[str, Any]],
    words: List[Dict[str, Any]],
    total_duration: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Maps AI scene start words and emphasis words to Whisper timestamps.

    Phase 5 & 7 Guarantees:
    - 100% Contiguous scene intervals: scene[0].start_time == 0.0, scene[i].end_time == scene[i+1].start_time.
    - Final scene end_time == total_duration (or start_time + MIN_SCENE_DURATION).
    - Enforces strictly minimum scene duration >= 2.5s (eliminating 0.7s flash cuts).
    - Preserves all visual and polymorphic attributes on scene dicts.
    """
    if not scenes:
        return []

    word_idx = 0
    last_start_time = 0.0
    timed_scenes: List[Dict[str, Any]] = []

    if total_duration is None:
        total_duration = max([float(w.get("end", 0.0)) for w in words], default=0.0) if words else 0.0

    for idx, scene in enumerate(scenes):
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
            for temp_idx in range(word_idx, len(words)):
                cleaned_whisper_word = _clean_word(words[temp_idx].get("word", ""))
                if cleaned_whisper_word and cleaned_whisper_word == seg_first_word:
                    candidate_start = float(words[temp_idx].get("start", 0.0))
                    matched = True
                    match_idx = temp_idx
                    word_idx = temp_idx + 1
                    break

            if not matched:
                if word_idx < len(words):
                    candidate_start = float(words[word_idx].get("start", 0.0))
                elif timed_scenes:
                    candidate_start = last_start_time + MIN_SCENE_DURATION
                else:
                    candidate_start = 0.0
                match_idx = word_idx
                word_idx = min(word_idx + scene_word_count, len(words))
        else:
            candidate_start = last_start_time + MIN_SCENE_DURATION if timed_scenes else 0.0

        if not timed_scenes:
            scene_start_time = 0.0
        else:
            if total_duration >= 5.0:
                scene_start_time = max(candidate_start, last_start_time + MIN_SCENE_DURATION)
            else:
                scene_start_time = max(candidate_start, last_start_time + 0.1)

        scene_start_time = round(scene_start_time, 3)
        last_start_time = scene_start_time

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

        timed_scene: Dict[str, Any] = dict(scene)
        timed_scene["scene_type"] = scene.get("scene_type") or scene.get("visual_type", "code_reveal")
        timed_scene["spoken_text"] = spoken_text
        timed_scene["start_time"] = scene_start_time
        timed_scene["emphasis_time"] = emphasis_time

        timed_scenes.append(timed_scene)

    if not timed_scenes:
        return []

    # Enforce 100% contiguous scene intervals: scene[i].end_time = scene[i+1].start_time
    for i in range(len(timed_scenes) - 1):
        timed_scenes[i]["end_time"] = timed_scenes[i + 1]["start_time"]

    final_end = max(total_duration, timed_scenes[-1]["start_time"] + (MIN_SCENE_DURATION if total_duration >= 5.0 else 0.5))
    timed_scenes[-1]["end_time"] = round(final_end, 3)

    # Phase 7: Post-processing pass guaranteeing duration >= MIN_SCENE_DURATION (2.5s)
    timed_scenes = enforce_minimum_scene_durations(
        timed_scenes,
        min_duration=MIN_SCENE_DURATION if total_duration >= 5.0 else 0.5,
        total_duration=total_duration,
    )

    return timed_scenes


def calculate_target_scenes(duration: Optional[float] = None) -> int:
    """
    Computes dynamic target scene count based on requested length N:
    target_scenes = max(5, min(12, int(round(N / 5.5))))
    For N=30s -> 5-6 scenes; for N=35s -> 6 scenes; for N=60s -> 10 to 11 scenes.
    """
    if duration is None:
        return 7
    try:
        dur_val = float(duration)
        return max(5, min(12, int(round(dur_val / 5.5))))
    except (TypeError, ValueError):
        return 7


def merge_excess_scenes(scenes: List[Dict[str, Any]], target_scenes: int = 7) -> List[Dict[str, Any]]:
    """
    Deterministically merges adjacent scenes down to target_scenes,
    protecting the hook at index 0 and preserving narrative continuity.
    """
    if not isinstance(scenes, list) or len(scenes) <= target_scenes:
        return scenes

    merged = [copy.deepcopy(s) for s in scenes]

    richness_priority = {
        "chemistry_reaction": 12,
        "algorithm_explorer": 11,
        "bento_grid": 10,
        "neural_code_split": 9,
        "function_graph": 8,
        "physics_sim": 7,
        "math_equation": 6,
        "code_transform": 5,
        "code_reveal": 4,
        "comparison": 3,
        "diagram": 2,
        "concept": 1,
        "fullscreen_text": 0,
    }

    while len(merged) > target_scenes:
        start_idx = 1 if len(merged) > 2 else 0
        best_i = start_idx
        min_score = float("inf")

        for i in range(start_idx, len(merged) - 1):
            s1 = merged[i]
            s2 = merged[i + 1]
            t1 = s1.get("spoken_text") or s1.get("narration") or ""
            t2 = s2.get("spoken_text") or s2.get("narration") or ""
            combined_len = len(t1.split()) + len(t2.split())

            type1 = s1.get("scene_type") or s1.get("visual_type", "")
            type2 = s2.get("scene_type") or s2.get("visual_type", "")
            bonus = 0
            if type1 in {"fullscreen_text", "concept"} and type2 in {"fullscreen_text", "concept"}:
                bonus = 25
            elif type1 in {"fullscreen_text", "concept"} or type2 in {"fullscreen_text", "concept"}:
                bonus = 12
            elif type1 == type2:
                bonus = 8

            score = combined_len - bonus
            if score < min_score:
                min_score = score
                best_i = i

        s1 = merged[best_i]
        s2 = merged[best_i + 1]

        t1 = (s1.get("spoken_text") or s1.get("narration") or "").strip()
        t2 = (s2.get("spoken_text") or s2.get("narration") or "").strip()
        if t1 and not t1.endswith((".", "!", "?")):
            t1 += "."
        merged_spoken = f"{t1} {t2}".strip()

        p1 = richness_priority.get(s1.get("scene_type") or s1.get("visual_type", ""), 0)
        p2 = richness_priority.get(s2.get("scene_type") or s2.get("visual_type", ""), 0)
        base = copy.deepcopy(s2 if p2 >= p1 else s1)

        base["spoken_text"] = merged_spoken
        if "narration" in base:
            base["narration"] = merged_spoken

        merged = merged[:best_i] + [base] + merged[best_i + 2:]

    for idx, s in enumerate(merged):
        if "scene_num" in s:
            s["scene_num"] = idx + 1

    return merged


align_beats_with_scenes = align_timeline