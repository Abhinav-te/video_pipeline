import re
import json
import os
import time
from google import genai
from google.genai import types

# GEMINI_API_KEY can be a single key or a comma-separated fallback chain,
# e.g. GEMINI_API_KEY="AIza...key1,AIza...key2"
# Quota is scoped to the Google Cloud PROJECT behind a key (not the key or
# your account), so a second key from a separate AI Studio project has its
# own independent free-tier pool. Multiple keys under the SAME project do
# NOT add quota — only a key from a genuinely different project does.
def get_api_keys():
    raw = os.environ["GEMINI_API_KEY"]
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("GEMINI_API_KEY is set but empty.")
    return keys


_clients = {}


def _get_client(api_key):
    if api_key not in _clients:
        _clients[api_key] = genai.Client(api_key=api_key)
    return _clients[api_key]

# GEMINI_MODEL can be a single model or a comma-separated fallback chain,
# e.g. GEMINI_MODEL="gemini-3.6-flash,gemini-flash-latest,gemini-3.5-flash"
# Quota (429 RESOURCE_EXHAUSTED) is generally tracked per-model, so falling
# through to the next model in the chain is the right move when one is
# exhausted — unlike a 503, retrying the SAME model won't help.
DEFAULT_MODEL_CHAIN = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]


def get_model_chain():
    raw = os.getenv("GEMINI_MODEL", "").strip()
    if not raw:
        return DEFAULT_MODEL_CHAIN
    models = [m.strip() for m in raw.split(",") if m.strip()]
    return models or DEFAULT_MODEL_CHAIN


def get_system_prompt(duration):
    if duration == 15:
        target_beats = "4 to 6 beats"
        word_limit = "Total spoken words: under 40 words."
    elif duration == 60:
        target_beats = "16 to 22 beats"
        word_limit = "Total spoken words: between 140 and 170 words."
    else:
        target_beats = "8 to 12 beats"
        word_limit = "Total spoken words: between 75 and 90 words."

    return f"""You are the director and scriptwriter for a high-retention Python educational short.
Your job is to architect the video by mapping the spoken script to rapid semantic visual beats.

AVAILABLE BEAT TYPES:
- "fullscreen_text": High-impact hook, reset, or single concept punch. Uses "display_text".
- "code_reveal": Introduces a new code block. Uses "code_snippet" and optional "focus_phrase" (exact substring to highlight).
- "code_transform": Updates/modifies code. Uses "code_snippet" and optional "focus_phrase".
- "terminal": Command line run or traceback output. Uses "code_snippet".
- "diagram": Conceptual flow using nodes. Uses "nodes" (2-3 items max).
- "comparison": Side-by-side / top-bottom fix. Uses "problem_label", "problem_code", "solution_label", "solution_code".

OUTPUT FORMAT: Strict JSON only matching this skeleton:
{{
  "title": "Short topic",
  "schema_version": "2.1",
  "scenes": [
    {{
      "scene_type": "fullscreen_text",
      "spoken_text": "This Python mistake will ruin your application.",
      "display_text": "THIS WILL RUIN YOUR APP",
      "emphasis_word": "ruin"
    }}
  ]
}}

EDITORIAL INTELLIGENCE RULES:
1. TARGET BEATS: Generate {target_beats}.
2. {word_limit}
3. STRICT WORD LIMIT PER BEAT: Each "spoken_text" MUST be between 5 and 11 words maximum. Never exceed 11 words in a single beat. Break explanations across multiple beats.
4. Scene 1 MUST be "fullscreen_text" with a curiosity gap hook.
5. Pacing: Never linger. The final takeaway beat must be under 8 words.
6. Write naturally for text-to-speech (use 'dunder' instead of '__').
7. CODE VALIDATION: Every "code_snippet" MUST parse as valid Python syntax. If revealing a partial function or loop, you MUST include "pass" or "..." to prevent IndentationErrors.
"""


def _call_model(client, model, contents, prompt, max_retries=4):
    """
    Calls one model. Retries with backoff on transient 503/UNAVAILABLE.
    Raises immediately (no retry) on 429/RESOURCE_EXHAUSTED so the caller
    can fall through to the next model right away.
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    response_mime_type="application/json",
                ),
            )
            raw_text = response.text.strip()
            # Strip markdown code fences if the model wrapped them
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE | re.IGNORECASE)
            raw_text = re.sub(r"```\s*$", "", raw_text, flags=re.MULTILINE).strip()
            # Extract first outer JSON object if extra text slipped in
            match = re.search(r"(\{.*\})", raw_text, flags=re.DOTALL)
            if match:
                raw_text = match.group(1)
            return json.loads(raw_text)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                raise  # quota issue — don't waste retries on the same model
            last_err = e
            if "503" in msg or "UNAVAILABLE" in msg:
                wait = 2 ** attempt  # 1s, 2s, 4s, 8s
                print(f"[ENGINE] ⚠️ {model} 503, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    raise last_err


def generate_script(topic, duration):
    """Generates the script using Gemini, walking a fallback chain of
    (API key × model) combinations.

    - 503/UNAVAILABLE on a model: retried with backoff on that same
      key+model.
    - 429/RESOURCE_EXHAUSTED (quota) on a model: skip to the next model
      in the chain for the SAME key first (cheap to try, quota is
      per-model). Only once every model is exhausted on the current key
      do we move to the next key, since a key from a different project
      has its own separate quota pool.
    """
    prompt = get_system_prompt(duration)
    contents = (
        f"Topic: {topic}. STRICT REQUIREMENT: Scene 1 MUST be 'fullscreen_text'. "
        f"You MUST also include at least one 'comparison' scene."
    )

    keys = get_api_keys()
    model_chain = get_model_chain()
    last_err = None

    for key_index, api_key in enumerate(keys):
        client = _get_client(api_key)
        key_label = f"key #{key_index + 1}/{len(keys)}"

        for i, model in enumerate(model_chain):
            try:
                print(f"[ENGINE] 🤖 Trying {model} on {key_label} ({i + 1}/{len(model_chain)})")
                return _call_model(client, model, contents, prompt)
            except Exception as e:
                last_err = e
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                    print(f"[ENGINE] ⚠️ {model} quota exhausted on {key_label}, trying next model...")
                    continue
                if "503" in msg or "UNAVAILABLE" in msg:
                    # Retries inside _call_model already failed. A 503 is
                    # specific to THIS model being overloaded right now —
                    # it says nothing about other models, so still worth
                    # trying the next one instead of giving up entirely.
                    print(f"[ENGINE] ⚠️ {model} still unavailable after retries on {key_label}, trying next model...")
                    continue
                # Some other, non-retryable error (e.g. bad request) — no
                # point trying other models/keys with the same broken request.
                raise

        print(f"[ENGINE] ⚠️ All models exhausted on {key_label}.")
        if key_index + 1 < len(keys):
            print("[ENGINE] 🔁 Switching to next API key (separate project quota)...")

    raise RuntimeError(
        f"All {len(keys)} key(s) × {len(model_chain)} model(s) exhausted or failed. "
        f"Last error: {last_err}"
    )