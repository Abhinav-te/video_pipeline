def align_timeline(scenes, words):
    """
    Maps the AI scene start words and emphasis words to exact Whisper timestamps.
    """
    word_idx = 0
    last_start_time = 0.0
    timed_scenes = []

    for scene in scenes:
        spoken_text = scene.get("spoken_text", "")
        if not spoken_text:
            continue

        # Isolate the first word to find the start time
        seg_first_word = spoken_text.split()[0].lower().strip(".,!?:;\"'")
        scene_start_time = last_start_time  # fallback: don't regress to 0.0
        matched = False

        temp_idx = word_idx
        while temp_idx < len(words):
            cleaned_whisper_word = words[temp_idx]["word"].lower().strip(".,!?:;\"'")
            if cleaned_whisper_word == seg_first_word:
                scene_start_time = words[temp_idx]["start"]
                word_idx = temp_idx
                matched = True
                break
            temp_idx += 1

        if not matched:
            # First word wasn't found ahead of the current cursor (transcription
            # mismatch, punctuation, etc). Don't leave word_idx stuck: advance it
            # past this scene's word count so the NEXT scene still searches
            # forward instead of re-scanning from a stale position. Keep the
            # start_time monotonic by falling back to the previous scene's time
            # rather than resetting to 0.0.
            word_idx = min(word_idx + len(spoken_text.split()), len(words))

        last_start_time = scene_start_time

        # Search for the emphasis timestamp
        emphasis_word = scene.get("emphasis_word", "").lower().strip(".,!?:;\"'")
        emphasis_time = scene_start_time

        if emphasis_word:
            search_idx = word_idx
            while search_idx < min(len(words), word_idx + len(spoken_text.split()) + 5):
                if words[search_idx]["word"].lower().strip(".,!?:;\"'") == emphasis_word:
                    emphasis_time = words[search_idx]["start"]
                    break
                search_idx += 1

        # Package the perfectly timed scene
        timed_scene = {
            "scene_type": scene.get("scene_type", "code_reveal"),
            "spoken_text": spoken_text,
            "start_time": scene_start_time,
            "emphasis_time": emphasis_time
        }

        # Dynamically carry over any visual properties (like focus_phrase, nodes, code_snippet)
        for key in ["display_text", "code_snippet", "nodes", "problem_label", "problem_code", "solution_label", "solution_code", "focus_phrase"]:
            if key in scene:
                timed_scene[key] = scene[key]

        timed_scenes.append(timed_scene)

    return timed_scenes