# Automated Technical Video Generation Engine

An end-to-end programmatic video pipeline that transforms technical coding topics into 9:16 vertical shorts (TikTok/Reels/Shorts) using an automated multi-stage architecture.

---

## System Architecture

The pipeline decouples content orchestration, syntax validation, speech synthesis, and frame rendering into distinct layers:

```text
TOPIC & DURATION
       │
       ▼
[ AI Director (Gemini API) ]
  • Enforces 5–11 words per semantic beat
  • Selects visual primitives (Code, Diagram, Terminal, Comparison)
  • Multi-key & multi-model fallback chain
       │
       ▼
[ Pre-Flight Validation ]
  • Python AST syntax parsing (ast.parse)
  • Markdown normalization & snippet linting
       │
       ▼
[ Speech Synthesis & Forced Alignment ]
  • Edge-TTS (Natural voiceover)
  • OpenAI Whisper (Word-level timestamps & emphasis mapping)
       │
       ▼
[ Video Compositing (Remotion / React) ]
  • 1080x1920 (9:16) high-density vertical layout
  • Dynamic word-by-word subtitle highlight window
  • Syntax highlighting & focus-phrase camera punch
       │
       ▼
upload_ready_short.mp4