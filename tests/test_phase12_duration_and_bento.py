import unittest
from engine.timeline.beats import calculate_target_scenes, merge_excess_scenes
from engine.timeline.choreographer import choreograph_scenes, resolve_domain
from engine.director.script import get_system_prompt
from engine.validation.schema import validate_script_plan


class TestPhase12DurationAndBento(unittest.TestCase):
    def test_duration_scaling_targets(self):
        """Verify target scenes and word formulas scale accurately to 60s."""
        # 30s -> ~5-6 scenes
        self.assertIn(calculate_target_scenes(30), [5, 6])
        # 35s -> 6 scenes
        self.assertEqual(calculate_target_scenes(35), 6)
        # 60s -> 11 scenes
        self.assertEqual(calculate_target_scenes(60), 11)

        # Director system prompt for 60s must enforce target words and scenes
        prompt_60 = get_system_prompt(duration=60, subject="electrical")
        self.assertIn("135", prompt_60)  # target_words = round(60 * 2.25) = 135
        self.assertIn("11", prompt_60)   # target_scenes = 11
        self.assertIn("between 120 and 150 words total", prompt_60)
        self.assertIn("11 and 18 words", prompt_60)

    def test_schema_validation_accepts_12_15_words_for_60s(self):
        """Verify polymorphic validator allows 12-15 words per scene for 60s scripts."""
        plan_60s = {
            "title": "Electrical Power Systems Masterclass",
            "subject": "electrical",
            "scenes": [
                {
                    "scene_index": i,
                    "title": f"Scene {i}",
                    "spoken_text": "This is a detailed and rich educational explanation covering circuit laws and theorems thoroughly for engineers.", # 16 words
                    "scene_type": "fullscreen_text" if i == 0 else ("bento_grid" if i == 9 else "electrical_grid"),
                    "display_text": "HOOK TITLE" if i == 0 else None,
                    "emphasis_word": "theorems",
                }
                for i in range(10)
            ],
            "total_scenes": 10,
            "duration": 60,
        }
        valid, errors = validate_script_plan(plan_60s)
        self.assertTrue(valid, f"Validation failed: {errors}")

    def test_choreographer_single_bento_and_no_back_to_back(self):
        """Verify choreographer on a 10-scene script NEVER repeats bento_grid and never repeats consecutive visuals."""
        raw_scenes = [
            {
                "scene_index": i,
                "title": f"Electrical Topic {i}",
                "spoken_text": f"Explanation for electrical engineering concept number {i} discussing power and impedance.",
                "narration": f"Narration for circuit section {i}.",
                "start_time": float(i * 5.5),
                "end_time": float((i + 1) * 5.5),
            }
            for i in range(10)
        ]
        words = [
            {"word": "electrical", "start": 0.0, "end": 0.5},
            {"word": "theorems", "start": 50.0, "end": 55.0},
        ]

        enriched = choreograph_scenes(raw_scenes, words, domain="electrical", fps=30)
        self.assertEqual(len(enriched), 10)

        # 1. Bento grid must appear strictly at index 9 (len - 1) and AT MOST ONCE
        bento_indices = [idx for idx, s in enumerate(enriched) if s.get("visual_type") == "bento_grid"]
        self.assertEqual(bento_indices, [9], f"bento_grid appeared at {bento_indices}, expected [9]")

        # 2. Scene 0 must be comparison hook
        self.assertEqual(enriched[0].get("visual_type"), "comparison")

        # 3. No consecutive identical visual_type + sub_mode
        for idx in range(1, len(enriched)):
            curr_v = enriched[idx].get("visual_type")
            prev_v = enriched[idx - 1].get("visual_type")
            curr_m = enriched[idx].get("sub_mode")
            prev_m = enriched[idx - 1].get("sub_mode")
            if curr_v == prev_v and curr_v in {"electrical_grid", "mechanics_fbd", "quantum_sim", "chemistry_reaction"}:
                self.assertNotEqual(curr_m, prev_m, f"Consecutive identical sub_mode '{curr_m}' at scenes {idx-1} and {idx}")

    def test_zero_ml_calculus_fallbacks_in_bento_and_graph(self):
        """Verify bento_data and graph_data contain subject-specific content with zero ML/Calculus fallbacks."""
        subjects = ["electrical", "mechanics", "quantum_physics", "chemistry"]

        for subj in subjects:
            raw_scenes = [
                {
                    "scene_index": i,
                    "title": f"{subj} Scene {i}",
                    "spoken_text": f"Discussion of {subj} principles and state transformations.",
                    "start_time": float(i * 5.0),
                    "end_time": float((i + 1) * 5.0),
                }
                for i in range(6)
            ]
            enriched = choreograph_scenes(raw_scenes, [], domain=subj, fps=30)

            # Check final bento_grid scene
            final_scene = enriched[-1]
            self.assertEqual(final_scene.get("visual_type"), "bento_grid")
            bento = final_scene.get("bento_data", {})
            self.assertIsNotNone(bento, f"Missing bento_data for {subj}")
            section_title = bento.get("section_title", "")
            self.assertNotIn("UNSUPERVISED ML", section_title, f"ML fallback found in {subj} bento title: {section_title}")
            cards = bento.get("cards", [])
            self.assertEqual(len(cards), 4, f"Expected 4 cards for {subj}, got {len(cards)}")
            card_types = [c.get("algo_type") for c in cards]
            self.assertNotIn("kmeans", card_types, f"K-Means found in {subj} cards")
            self.assertNotIn("dbscan", card_types, f"DBSCAN found in {subj} cards")

            # Check function_graph scene
            graph_scenes = [s for s in enriched if s.get("visual_type") == "function_graph"]
            self.assertTrue(len(graph_scenes) >= 1, f"Expected function_graph in {subj}")
            for gs in graph_scenes:
                graph_data = gs.get("graph_data", {})
                header = graph_data.get("header", "")
                title = graph_data.get("title", "")
                self.assertNotIn("CALCULUS • ANALYTIC GEOMETRY", header, f"Calculus fallback found in {subj} header: {header}")
                curves = graph_data.get("curves", [])
                curve_labels = [c.get("label", "") for c in curves]
                for cl in curve_labels:
                    self.assertNotIn("x^2 / 4", cl, f"Calculus parabola found in {subj} curve label: {cl}")


if __name__ == "__main__":
    unittest.main()
