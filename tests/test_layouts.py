import unittest

import numpy as np

from app.rl.layouts import LayoutConfig, generate_layout


class LayoutTests(unittest.TestCase):
    def test_preset_layout_matches_existing_default(self):
        layout = generate_layout(LayoutConfig(mode="preset", room_size=10.0, dirt_count=3), seed=0)
        np.testing.assert_allclose(layout.robot, np.array([1.0, 1.0], dtype=np.float32))
        self.assertEqual(layout.heading, 0.0)
        np.testing.assert_allclose(
            layout.dirt,
            np.array([[8.0, 8.0], [2.0, 7.0], [7.0, 2.0]], dtype=np.float32),
        )
        self.assertEqual(layout.obstacles, [])

    def test_random_layout_reproducible_by_seed(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=5, obstacle_count=2)
        a = generate_layout(config, seed=123)
        b = generate_layout(config, seed=123)
        np.testing.assert_allclose(a.robot, b.robot)
        np.testing.assert_allclose(a.dirt, b.dirt)
        self.assertEqual(a.obstacles, b.obstacles)

    def test_random_layout_changes_across_seeds(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=5, obstacle_count=2)
        a = generate_layout(config, seed=123)
        b = generate_layout(config, seed=124)
        self.assertFalse(np.allclose(a.dirt, b.dirt))

    def test_generated_positions_have_clearance(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=20, obstacle_count=4, min_clearance=0.6)
        layout = generate_layout(config, seed=9)
        self.assertTrue(np.all(layout.dirt >= 0.5))
        self.assertTrue(np.all(layout.dirt <= 9.5))
        for dirt in layout.dirt:
            self.assertGreaterEqual(np.linalg.norm(dirt - layout.robot), config.min_clearance)


if __name__ == "__main__":
    unittest.main()
