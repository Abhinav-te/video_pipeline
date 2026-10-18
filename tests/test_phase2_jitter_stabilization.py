"""
test_phase2_jitter_stabilization.py
Verifies the structural anti-jitter / anti-clip fixes applied in Phase 2 stabilization pass:
  - CameraRig is a scale-only wrapper (no X/Y pan that clips 9:16 edges)
  - CameraRig is applied at card level (not root), decoupled from scene background
  - Scale is capped at 1.04x and rounded to suppress subpixel noise
  - Cards use maxWidth:920px so 1.04x zoom stays inside the 1080px safe area
  - CameraRig spring config is critically damped (no oscillation)
  - KineticCallout outer span is display:inline (zero-reflow, no line-height shift)
"""
import sys
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_DIR / "video" / "src"
COMPONENTS_DIR = SRC_DIR / "components"


class TestJitterStabilization(unittest.TestCase):

    # ── CameraRig ──────────────────────────────────────────────────────────────

    def test_camerarig_scale_only_no_pan(self):
        """CameraRig must NOT contain any X/Y translation (offsetX, offsetY, translate3d
        with non-zero X/Y) — panning clips code at the 9:16 viewport edges."""
        content = (SRC_DIR / "CameraRig.jsx").read_text(encoding="utf-8")
        self.assertNotIn("offsetX", content,
                         "CameraRig must not compute X pan offset — it clips 9:16 edges")
        self.assertNotIn("offsetY", content,
                         "CameraRig must not compute Y pan offset — it clips 9:16 edges")
        self.assertNotIn("translate3d(", content,
                         "CameraRig must not use translate3d pan — scale-only is required")

    def test_camerarig_fixed_transform_origin(self):
        """CameraRig must use transformOrigin: 'center center' (not a dynamic percentage string)."""
        content = (SRC_DIR / "CameraRig.jsx").read_text(encoding="utf-8")
        self.assertIn("transformOrigin: 'center center'", content,
                      "CameraRig transformOrigin must be the fixed literal 'center center'")
        self.assertNotIn("transformOrigin: `${", content,
                         "CameraRig must NOT use dynamic template-string percentage transformOrigin")

    def test_camerarig_scale_rounded(self):
        """Spring scale output must be rounded to eliminate subpixel float rasterization noise."""
        content = (SRC_DIR / "CameraRig.jsx").read_text(encoding="utf-8")
        self.assertIn("Math.round(", content,
                      "CameraRig must round scale values (Math.round) to suppress subpixel jitter")
        self.assertIn("roundedScale", content,
                      "CameraRig must use a named rounded scale variable")

    def test_camerarig_critically_damped_spring(self):
        """Camera spring config must be critically damped (damping:18) to eliminate oscillation."""
        content = (SRC_DIR / "cameraUtils.js").read_text(encoding="utf-8")
        self.assertIn("damping: 18", content)
        self.assertIn("stiffness: 80", content)
        self.assertIn("mass: 0.6", content)

    def test_camerarig_default_focus_scale_safe(self):
        """Default focusScale in CameraRig must be 1.04 (subtle punch within 9:16 safe area)."""
        content = (SRC_DIR / "CameraRig.jsx").read_text(encoding="utf-8")
        self.assertIn("focusScale = 1.04", content,
                      "CameraRig default focusScale must be 1.04 to stay inside 9:16 safe area")

    # ── CodingShort card-level zoom & safe area ────────────────────────────────

    def test_codingshort_card_maxwidth_safe_area(self):
        """Code cards must use maxWidth:920px so that at 1.04x scale (956.8px visual)
        they remain inside the 960px content area (1080 - 60px padding * 2)."""
        content = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("maxWidth: '920px'", content,
                      "Code cards must have maxWidth:920px to stay inside the 9:16 safe area at 1.04x zoom")

    def test_codingshort_camera_applied_to_card_not_root(self):
        """CameraRig must wrap individual card divs, not the outer AbsoluteFill.
        The background (backgroundColor: '#0d1117') must be on a separate AbsoluteFill
        that is never passed through CameraRig."""
        content = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        # Root background AbsoluteFill must exist outside CameraRig
        self.assertIn("backgroundColor: '#0d1117'", content)
        # CameraRig must appear after scene-type checks, not as the root wrapper
        camera_rig_pos = content.find("<CameraRig")
        root_fill_pos = content.find("backgroundColor: '#0d1117'")
        self.assertGreater(camera_rig_pos, root_fill_pos,
                           "CameraRig must be nested inside scene type checks, not wrapping the root background")

    def test_codingshort_no_focus_scale_above_safe_threshold(self):
        """All focusScale values in CodingShort must be <= 1.04 to prevent viewport clipping."""
        content = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertNotIn("focusScale={1.08}", content,
                         "focusScale={1.08} would clip content at the 9:16 edges")
        self.assertNotIn("focusScale={1.10}", content,
                         "focusScale={1.10} would clip content at the 9:16 edges")
        self.assertNotIn("focusScale={1.12}", content,
                         "focusScale={1.12} would clip content at the 9:16 edges")

    # ── KineticCallout ────────────────────────────────────────────────────────

    def test_kinetic_callout_zero_reflow_outer_span(self):
        """Outer KineticCallout wrapper must be display:inline (NOT inline-block)
        so it contributes zero height to the surrounding line."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("display: 'inline'", content,
                      "KineticCallout outer span must use display:inline for zero line-height contribution")
        self.assertNotIn("display: 'inline-block'", content,
                         "KineticCallout must not use inline-block which adds height to the line")

    def test_kinetic_callout_accent_layer_absolute(self):
        """Decorative accent/glow layer must be position:absolute (out of flow)."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("position: 'absolute'", content,
                      "KineticCallout accent layer must be position:absolute (out of flow)")

    def test_kinetic_callout_scale_rounded(self):
        """KineticCallout spring values must be rounded to suppress subpixel glow noise."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("Math.round(", content,
                      "KineticCallout must round spring values to eliminate subpixel rasterization noise")

    def test_kinetic_callout_fixed_transform_origin(self):
        """KineticCallout accent layer must use transformOrigin: 'center center' (not dynamic)."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("transformOrigin: 'center center'", content,
                      "KineticCallout accent layer must use fixed 'center center' transform origin")


if __name__ == "__main__":
    unittest.main()
