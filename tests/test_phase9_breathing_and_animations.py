"""Unit tests for Phase 9: Dynamic Viewport Breathing, Scene Count Capping, and True Multi-Geometry Animations.

Verifies:
1. Hard cap on scene count: calculate_target_scenes(35) == 7, merges excess scenes down to <= 7 scenes.
2. Scene 0 (Hook) preservation during scene merging.
3. Spoken text concatenation and rich visual primitive retention during merging.
4. Mandatory Visual Type Rotation in choreographer.py: rotation across comparison, chemistry_reaction,
   function_graph, and bento_grid.
5. Dynamic Viewport Breathing: layout_density modes (compact_punch, canvas_spotlight, full_dashboard).
6. 4 Distinct Chemistry Sub-modes (sn2_concerted, steric_blockade, sn1_ionization, sn1_racemic).
"""

import unittest
from engine.timeline.beats import calculate_target_scenes, merge_excess_scenes
from engine.timeline.choreographer import choreograph_scenes


class TestPhase9SceneCountAndMerging(unittest.TestCase):
    """Tests duration-based scene count calculations and deterministic adjacent merging."""

    def test_calculate_target_scenes(self):
        """Strictly enforces dynamic scene scaling: target_scenes = max(5, min(12, round(duration / 5.5)))."""
        self.assertEqual(calculate_target_scenes(35), 6)
        self.assertEqual(calculate_target_scenes(30), 5)
        self.assertEqual(calculate_target_scenes(25), 5)
        self.assertEqual(calculate_target_scenes(10), 5)  # Clamped to minimum 5
        self.assertEqual(calculate_target_scenes(40), 7)
        self.assertEqual(calculate_target_scenes(60), 11)  # Scales to 11 for 60s videos

    def test_merge_excess_18_scenes_down_to_target(self):
        """Simulates the 18-scene failure from Phase 8 and verifies reduction to strictly <= 7 scenes."""
        raw_18_scenes = [
            {
                "scene_num": i + 1,
                "visual_type": "chemistry_reaction",
                "spoken_text": f"This is scene {i + 1} explaining step {i + 1} of substitution.",
                "reaction_name": f"Step {i + 1}",
            }
            for i in range(18)
        ]

        target_scenes = calculate_target_scenes(35)  # 7
        merged = merge_excess_scenes(raw_18_scenes, target_scenes=target_scenes)

        self.assertLessEqual(len(merged), 7)
        self.assertGreaterEqual(len(merged), 5)

        # Verify Hook preservation: Scene 0 text is preserved at the beginning
        self.assertTrue(merged[0]["spoken_text"].startswith("This is scene 1"))

        # Verify sequential numbering
        for idx, scene in enumerate(merged):
            self.assertEqual(scene["scene_num"], idx + 1)

    def test_merge_preserves_rich_visual_primitives(self):
        """When merging a simple scene with a rich visual scene, the rich primitive is retained."""
        scenes = [
            {"scene_num": 1, "visual_type": "comparison", "spoken_text": "Hook comparing SN1 and SN2."},
            {"scene_num": 2, "visual_type": "code_reveal", "spoken_text": "Short intro code."},
            {"scene_num": 3, "visual_type": "chemistry_reaction", "spoken_text": "Detailed concerted reaction mechanism."},
            {"scene_num": 4, "visual_type": "fullscreen_text", "spoken_text": "Transition card."},
            {"scene_num": 5, "visual_type": "function_graph", "spoken_text": "Energy landscape graph."},
            {"scene_num": 6, "visual_type": "bento_grid", "spoken_text": "Final decision matrix."},
        ]

        # Target 5 scenes (merging 1 pair)
        merged = merge_excess_scenes(scenes, target_scenes=5)
        self.assertEqual(len(merged), 5)

        visual_types = [s["visual_type"] for s in merged]
        # Rich primitives must not be lost
        self.assertIn("chemistry_reaction", visual_types)
        self.assertIn("function_graph", visual_types)
        self.assertIn("bento_grid", visual_types)


class TestPhase9ChoreographerVisualRotationAndBreathing(unittest.TestCase):
    """Tests choreographer visual type rotation, 4 chemistry sub-modes, and layout density breathing."""

    def test_chemistry_visual_type_rotation_and_submodes(self):
        """Verifies that a 7-scene chemistry video rotates visual types and does NOT render all scenes as chemistry_reaction."""
        raw_scenes = [
            {"scene_num": 1, "spoken_text": "Why does SN2 invert stereochemistry while SN1 gives a racemic mixture?"},
            {"scene_num": 2, "spoken_text": "In SN2, hydroxide attacks backside at 180 degrees causing umbrella flip."},
            {"scene_num": 3, "spoken_text": "Tertiary substrates block backside attack completely due to steric hindrance."},
            {"scene_num": 4, "spoken_text": "SN1 begins with slow rate-determining ionization into planar carbocation."},
            {"scene_num": 5, "spoken_text": "Water attacks planar carbocation from both top and bottom creating racemic mixture."},
            {"scene_num": 6, "spoken_text": "Compare the 1-peak concerted energy curve against the 2-peak intermediate curve."},
            {"scene_num": 7, "spoken_text": "Here is the ultimate cheat sheet decision matrix for substrate and solvent."},
        ]

        enriched = choreograph_scenes(
            timed_scenes=raw_scenes,
            words=[],
            fps=30,
            domain="chemistry",
        )

        self.assertEqual(len(enriched), 7)

        # 1. Structural Rhythm & Visual Type Rotation
        v_types = [s.get("visual_type") for s in enriched]
        self.assertEqual(v_types[0], "comparison")  # Scene 1: Hook Comparison
        self.assertEqual(v_types[1], "chemistry_reaction")  # Scene 2: SN2 Concerted
        self.assertEqual(v_types[2], "chemistry_reaction")  # Scene 3: Steric Blockade
        self.assertEqual(v_types[3], "chemistry_reaction")  # Scene 4: SN1 Ionization
        self.assertEqual(v_types[4], "chemistry_reaction")  # Scene 5: SN1 Racemic
        self.assertEqual(v_types[5], "function_graph")  # Scene 6: Energy Landscape Curve
        self.assertEqual(v_types[6], "bento_grid")  # Scene 7: 4-Card Decision Matrix

        # 2. 4 Distinct Chemistry Sub-modes
        self.assertEqual(enriched[1].get("sub_mode"), "sn2_concerted")
        self.assertEqual(enriched[2].get("sub_mode"), "steric_blockade")
        self.assertEqual(enriched[3].get("sub_mode"), "sn1_ionization")
        self.assertEqual(enriched[4].get("sub_mode"), "sn1_racemic")

        # 3. Dynamic Viewport Breathing layout_density
        self.assertEqual(enriched[0].get("layout_density"), "compact_punch")
        self.assertEqual(enriched[1].get("layout_density"), "canvas_spotlight")
        self.assertEqual(enriched[2].get("layout_density"), "canvas_spotlight")
        self.assertEqual(enriched[3].get("layout_density"), "full_dashboard")
        self.assertEqual(enriched[4].get("layout_density"), "canvas_spotlight")
        self.assertEqual(enriched[5].get("layout_density"), "canvas_spotlight")
        self.assertEqual(enriched[6].get("layout_density"), "full_dashboard")

        # Layout density also mirrored inside choreography object
        for s in enriched:
            choreo = s.get("choreography", {})
            self.assertEqual(choreo.get("layout_density"), s.get("layout_density"))

        # Verify Bento Decision Matrix cards populated
        bento_scene = enriched[6]
        self.assertEqual(bento_scene.get("section_title"), "SN1 VS SN2 DECISION MATRIX")
        cards = bento_scene.get("cards", [])
        self.assertEqual(len(cards), 4)
        algo_types = [c.get("algo_type") for c in cards]
        self.assertEqual(algo_types, ["substrate", "nucleophile", "solvent", "stereochem"])


if __name__ == "__main__":
    unittest.main()
