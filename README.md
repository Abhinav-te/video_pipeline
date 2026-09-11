# Automated Technical Video Generation Engine

An end-to-end programmatic video pipeline that transforms technical coding topics into 9:16 vertical shorts (TikTok/Reels/Shorts) using an automated multi-stage architecture.

---

## System Architecture

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
Visual Primitives Supported
fullscreen_text: High-impact curiosity hooks and concept resets.

code_reveal: Progressive syntax-highlighted code block mounting.

code_transform: In-place modification of existing functions and logic.

terminal: Interactive command runs and traceback demonstrations.

diagram: Dynamic flowchart-style node graphs for algorithmic flow.

comparison: Side-by-side / top-bottom bug-vs-fix comparisons.

Prerequisites
Python: 3.10+ (tested on Python 3.11 / Ubuntu WSL2)

Node.js: v20+ LTS

FFmpeg: System-level binary installed

Gemini API Key: From Google AI Studio

Quickstart
1. Environment Setup
Bash
git clone [https://github.com/Abhinav-te/video_pipeline.git](https://github.com/Abhinav-te/video_pipeline.git)
cd video_pipeline

python3 -m venv engine/.venv
source engine/.venv/bin/activate
pip install -r requirements.txt

cd video
npm install
cd ..
2. Configure Environment Variables
Bash
export GEMINI_API_KEY="your_gemini_api_key"
3. Generate a Video
Bash
python3 generate_and_render.py --topic "Python Two Sum LeetCode solution" --length 60
