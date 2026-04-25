import unittest

import numpy as np

from app.rl.layouts import CircleObstacle
from app.rl.sensors import cast_lidar_rays, dirt_proximity_vector, local_dirt_signal


class SensorTests(unittest.TestCase):
    def test_lidar_detects_nearest_wall_ahead(self):
        readings = cast_lidar_rays(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            room_size=10.0,
            obstacles=[],
            ray_count=4,
            max_range=5.0,
        )
        self.assertEqual(readings.shape, (4,))
        self.assertAlmostEqual(readings[0], 1.0)

    def test_lidar_detects_circle_obstacle_before_wall(self):
        readings = cast_lidar_rays(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            room_size=10.0,
            obstacles=[CircleObstacle(x=3.0, y=1.0, radius=0.5)],
            ray_count=8,
            max_range=5.0,
        )
        self.assertLess(readings[0], 0.4)

    def test_local_dirt_signal_only_detects_nearby_dirt(self):
        dirt = np.array([[1.2, 1.1], [8.0, 8.0]], dtype=np.float32)
        self.assertEqual(
            local_dirt_signal(np.array([1.0, 1.0], dtype=np.float32), dirt, radius=0.4),
            1.0,
        )
        self.assertEqual(
            local_dirt_signal(np.array([5.0, 5.0], dtype=np.float32), dirt, radius=0.4),
            0.0,
        )

    def test_dirt_proximity_vector_reports_nearby_dirt_in_robot_frame(self):
        dirt = np.array([[3.0, 1.0], [8.0, 8.0]], dtype=np.float32)

        vector = dirt_proximity_vector(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            dirt=dirt,
            radius=4.0,
        )

        self.assertEqual(vector.shape, (3,))
        self.assertGreater(vector[0], 0.0)
        self.assertAlmostEqual(vector[1], 0.0, places=5)
        self.assertGreater(vector[2], 0.0)

    def test_dirt_proximity_vector_is_zero_when_dirt_is_out_of_range(self):
        vector = dirt_proximity_vector(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            dirt=np.array([[8.0, 8.0]], dtype=np.float32),
            radius=2.0,
        )

        np.testing.assert_allclose(vector, np.zeros(3, dtype=np.float32))

    def test_dirt_proximity_vector_ignores_dirt_blocked_by_obstacle(self):
        vector = dirt_proximity_vector(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            dirt=np.array([[3.0, 1.0]], dtype=np.float32),
            radius=4.0,
            obstacles=[CircleObstacle(x=2.0, y=1.0, radius=0.4)],
        )

        np.testing.assert_allclose(vector, np.zeros(3, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
