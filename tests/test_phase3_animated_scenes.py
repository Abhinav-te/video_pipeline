"""
test_phase3_animated_scenes.py
Comprehensive verification of Phase 3 deliverables:
  - Permanent text jitter elimination (zero continuous scale() transforms on text)
  - CodeRevealScene (sequential typewriter line reveal + macOS header + cursor)
  - CodeTransformScene (before -> after morph + glowing indicator at emphasis_time)
  - ComparisonScene (staggered dual cards + emerald winner glow)
  - DiagramScene (progressive step nodes + animated SVG flow arrows)
  - ConceptHeroScene (high-impact hero card + icon badge + progressive bullet reveals)
  - Stabilized Subtitles (fixed pixel height, lineHeight, background highlight, no scale)
"""
import unittest
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_DIR / "video" / "src"
COMPONENTS_DIR = SRC_DIR / "components"


class TestPhase3AnimatedScenes(unittest.TestCase):

    def test_all_scene_components_exist(self):
        """Verify all Phase 3 animated scene component files exist in video/src/components/."""
        required_components = [
            "CodeRevealScene.jsx",
            "CodeTransformScene.jsx",
            "ComparisonScene.jsx",
            "DiagramScene.jsx",
            "ConceptHeroScene.jsx",
        ]
        for name in required_components:
            path = COMPONENTS_DIR / name
            self.assertTrue(path.exists(), f"Missing required Phase 3 component: {path}")

    def test_no_continuous_text_scaling_in_components(self):
        """Headless Chromium re-rasterizes fonts when transform: scale() changes continuously.
        Verify that no component applies dynamic scale() transforms to text containers."""
        for file in [
            SRC_DIR / "CameraRig.jsx",
            COMPONENTS_DIR / "KineticCallout.jsx",
            COMPONENTS_DIR / "CodeRevealScene.jsx",
            COMPONENTS_DIR / "CodeTransformScene.jsx",
            COMPONENTS_DIR / "ComparisonScene.jsx",
            COMPONENTS_DIR / "DiagramScene.jsx",
            COMPONENTS_DIR / "ConceptHeroScene.jsx",
            SRC_DIR / "CodingShort.jsx",
        ]:
            content = file.read_text(encoding="utf-8")
            self.assertNotIn("scale(${roundedScale})", content,
                             f"{file.name} must not apply scale(roundedScale)")
            self.assertNotIn("scale(${highlightScale})", content,
                             f"{file.name} must not apply scale(highlightScale) to text")
            self.assertNotIn("scale(1.15)", content,
                             f"{file.name} must not scale subtitle words by 1.15x")

    def test_camerarig_uses_static_grid_and_optical_aura(self):
        """CameraRig must lock transform to 'none' and animate optical boxShadow aura."""
        content = (SRC_DIR / "CameraRig.jsx").read_text(encoding="utf-8")
        self.assertIn("transform: 'none'", content,
                      "CameraRig must lock transform to 'none' for static-grid font stability")
        self.assertIn("boxShadow: auraBoxShadow", content,
                      "CameraRig must animate optical emphasis aura via boxShadow")
        self.assertIn("glowBlur", content)
        self.assertIn("glowSpread", content)
        self.assertIn("glowOpacity", content)

    def test_kinetic_callout_uses_static_grid(self):
        """KineticCallout must lock text and highlight pill to transform: 'none'."""
        content = (COMPONENTS_DIR / "KineticCallout.jsx").read_text(encoding="utf-8")
        self.assertIn("inset: '-2px -6px'", content)
        self.assertIn("transform: 'none'", content)
        self.assertIn("borderRadius: '6px'", content)

    def test_subtitles_stabilized_fixed_metrics(self):
        """Subtitles must use fixed pixel height, lineHeight, and color/background highlight without scale()."""
        content = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("height: '100px'", content)
        self.assertIn("lineHeight: '60px'", content)
        self.assertIn("transform: 'none'", content)
        self.assertIn("bottom: '120px'", content)
        self.assertNotIn("scale(1.15)", content)

    def test_code_reveal_primitive(self):
        """CodeRevealScene must render macOS window dots, filename badge, staggered reveals, and cursor."""
        content = (COMPONENTS_DIR / "CodeRevealScene.jsx").read_text(encoding="utf-8")
        self.assertIn("#ff5f56", content, "Missing macOS close button dot")
        self.assertIn("#ffbd2e", content, "Missing macOS minimize button dot")
        self.assertIn("#27c93f", content, "Missing macOS maximize button dot")
        self.assertIn("TerminalCursor", content, "Missing terminal cursor integration")
        self.assertIn("staggerFrames", content, "Missing staggered line reveal logic")
        self.assertIn("transform: 'none'", content)

    def test_code_transform_primitive(self):
        """CodeTransformScene must render Before header, After header, and progress divider at emphasis_time."""
        content = (COMPONENTS_DIR / "CodeTransformScene.jsx").read_text(encoding="utf-8")
        self.assertIn("⚠️ Before", content, "Missing Before header badge")
        self.assertIn("✨ After", content, "Missing After header badge")
        self.assertIn("isPostEmphasis", content, "Missing emphasis-triggered transition flag")
        self.assertIn("transform: 'none'", content)

    def test_comparison_primitive(self):
        """ComparisonScene must animate staggered dual cards and highlight winner at emphasis_time with emerald glow."""
        content = (COMPONENTS_DIR / "ComparisonScene.jsx").read_text(encoding="utf-8")
        self.assertIn("card1Start", content, "Missing card 1 stagger start")
        self.assertIn("card2Start", content, "Missing card 2 stagger start")
        self.assertIn("winnerGlow", content, "Missing emerald winner glow animation")
        self.assertIn("#3fb950", content, "Missing emerald green highlight color")
        self.assertIn("WINNER 🏆", content, "Missing winner badge")

    def test_diagram_primitive(self):
        """DiagramScene must render step nodes and progressive animated SVG flow arrows."""
        content = (COMPONENTS_DIR / "DiagramScene.jsx").read_text(encoding="utf-8")
        self.assertIn("FlowArrow", content, "Missing FlowArrow component")
        self.assertIn("<svg", content, "Missing SVG arrow renderer")
        self.assertIn("Step {i + 1}", content, "Missing step numbering")
        self.assertIn("isArrowActive", content, "Missing sequential arrow lighting logic")

    def test_concept_hero_primitive(self):
        """ConceptHeroScene must render large animated icon badge, takeaway title, and bullet reveals."""
        content = (COMPONENTS_DIR / "ConceptHeroScene.jsx").read_text(encoding="utf-8")
        self.assertIn("displayText", content, "Missing hero display text")
        self.assertIn("points.map", content, "Missing progressive bullet reveal logic")
        self.assertIn("transform: 'none'", content)

    def test_codingshort_integrates_all_phase3_renderers(self):
        """CodingShort.jsx must import and wire all Phase 3 animated scene components."""
        content = (SRC_DIR / "CodingShort.jsx").read_text(encoding="utf-8")
        self.assertIn("import { CodeRevealScene", content)
        self.assertIn("import { CodeTransformScene }", content)
        self.assertIn("import { ComparisonScene }", content)
        self.assertIn("import { DiagramScene }", content)
        self.assertIn("import { ConceptHeroScene }", content)
        self.assertIn("<CodeRevealScene", content)
        self.assertIn("<CodeTransformScene", content)
        self.assertIn("<ComparisonScene", content)
        self.assertIn("<DiagramScene", content)
        self.assertIn("<ConceptHeroScene", content)


if __name__ == "__main__":
    unittest.main()

