from __future__ import annotations

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from app.rl.layouts import CircleObstacle, LayoutConfig, generate_layout
from app.rl.sensors import cast_lidar_rays, dirt_proximity_vector, local_dirt_signal


class DirtSeekingEnv(gym.Env):
    """Curriculum environment for finding nearby dirt, not full-room cleaning."""

    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(
        self,
        room_size: float = 10.0,
        max_steps: int = 200,
        dirt_count: int = 3,
        clean_radius: float = 0.35,
        forward_step: float = 0.3,
        turn_angle: float = 0.3,
        seed: int | None = None,
        render_mode: str | None = None,
        layout_mode: str = "random",
        obstacle_count: int = 1,
        lidar_rays: int = 8,
        dirt_sensor_radius: float = 4.0,
    ):
        super().__init__()

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"Unsupported render_mode: {render_mode}")

        self.size = float(room_size)
        self.max_steps = int(max_steps)
        self.dirt_count = int(dirt_count)
        self.clean_radius = float(clean_radius)
        self.forward_step = float(forward_step)
        self.turn_angle = float(turn_angle)
        self.render_mode = render_mode
        self.layout_mode = layout_mode
        self.obstacle_count = int(obstacle_count)
        self.lidar_rays = int(lidar_rays)
        self.dirt_sensor_radius = float(dirt_sensor_radius)

        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.ones(7 + self.lidar_rays, dtype=np.float32),
            high=np.ones(7 + self.lidar_rays, dtype=np.float32),
            dtype=np.float32,
        )

        self.rng = np.random.default_rng(seed)
        self.robot = np.zeros(2, dtype=np.float32)
        self.heading = 0.0
        self.dirt = np.empty((0, 2), dtype=np.float32)
        self.obstacles: list[CircleObstacle] = []
        self.steps = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if seed is not None:
            self.rng = np.random.default_rng(seed)

        layout_seed = seed
        if layout_seed is None and self.layout_mode == "random":
            layout_seed = int(self.rng.integers(0, np.iinfo(np.int32).max))

        layout = generate_layout(
            LayoutConfig(
                mode=self.layout_mode,
                room_size=self.size,
                dirt_count=self.dirt_count,
                obstacle_count=self.obstacle_count,
            ),
            seed=layout_seed,
        )

        self.robot = layout.robot.copy()
        self.heading = float(layout.heading)
        self.dirt = layout.dirt.copy()
        self.obstacles = list(layout.obstacles)
        self.steps = 0

        return self._obs(), self._info(
            hit_wall=False,
            hit_obstacle=False,
            found_dirt=False,
            reward_components=self._empty_reward_components(),
            nearest_dirt_distance=self._nearest_visible_dirt_distance(),
        )

    def step(self, action):
        self.steps += 1
        reward_components = self._empty_reward_components()
        previous_robot = self.robot.copy()
        previous_visible_distance = self._nearest_visible_dirt_distance()

        if action == 0:
            direction = np.array([np.cos(self.heading), np.sin(self.heading)], dtype=np.float32)
            self.robot = self.robot + (direction * self.forward_step)
        elif action == 1:
            self.heading += self.turn_angle
        elif action == 2:
            self.heading -= self.turn_angle

        self.heading = self._normalize_heading(self.heading)

        hit_wall = bool(np.any(self.robot < 0.0) or np.any(self.robot > self.size))
        if hit_wall:
            self.robot = previous_robot
            reward_components["wall_penalty"] = -2.0

        hit_obstacle = self._hits_obstacle(self.robot)
        if hit_obstacle:
            self.robot = previous_robot
            reward_components["obstacle_penalty"] = -3.0

        current_vector = self._dirt_proximity_vector()
        dirt_visible = bool(current_vector[2] > 0.0)
        if dirt_visible:
            reward_components["dirt_visible"] = 0.005

        current_visible_distance = self._nearest_visible_dirt_distance()
        if (
            action == 0
            and previous_visible_distance is not None
            and current_visible_distance is not None
        ):
            progress = previous_visible_distance - current_visible_distance
            reward_components["dirt_progress"] = progress * 1.5

        found_dirt = False
        if len(self.dirt) > 0:
            distances = np.linalg.norm(self.dirt - self.robot, axis=1)
            found_indices = np.flatnonzero(distances <= self.clean_radius)
            if len(found_indices) > 0:
                found_dirt = True
                reward_components["found_dirt"] = 5.0
                self.dirt = np.delete(self.dirt, found_indices, axis=0)

        terminated = found_dirt
        truncated = self.steps >= self.max_steps
        reward = float(sum(reward_components.values()))
        info = self._info(
            hit_wall=hit_wall,
            hit_obstacle=hit_obstacle,
            found_dirt=found_dirt,
            reward_components=reward_components,
            nearest_dirt_distance=current_visible_distance,
        )

        return self._obs(), reward, terminated, truncated, info

    def _obs(self):
        lidar_readings = cast_lidar_rays(
            robot=self.robot,
            heading=self.heading,
            room_size=self.size,
            obstacles=self.obstacles,
            ray_count=self.lidar_rays,
        )
        dirt_vector = self._dirt_proximity_vector()
        remaining_step_fraction = 1.0 - (self.steps / max(self.max_steps, 1))
        return np.array(
            [
                np.sin(self.heading),
                np.cos(self.heading),
                local_dirt_signal(self.robot, self.dirt, radius=self.clean_radius),
                *dirt_vector,
                *lidar_readings,
                np.clip(remaining_step_fraction, 0.0, 1.0),
            ],
            dtype=np.float32,
        )

    def _dirt_proximity_vector(self):
        return dirt_proximity_vector(
            robot=self.robot,
            heading=self.heading,
            dirt=self.dirt,
            radius=self.dirt_sensor_radius,
            obstacles=self.obstacles,
        )

    def _nearest_visible_dirt_distance(self):
        if len(self.dirt) == 0:
            return None

        vectors = self.dirt - self.robot
        distances = np.linalg.norm(vectors, axis=1)
        visible_distances = [
            float(distance)
            for index, distance in enumerate(distances)
            if float(distance) <= self.dirt_sensor_radius
            and dirt_proximity_vector(
                robot=self.robot,
                heading=self.heading,
                dirt=self.dirt[index : index + 1],
                radius=self.dirt_sensor_radius,
                obstacles=self.obstacles,
            )[2]
            > 0.0
        ]
        if not visible_distances:
            return None
        return min(visible_distances)

    def _info(
        self,
        *,
        hit_wall: bool,
        hit_obstacle: bool,
        found_dirt: bool,
        reward_components: dict[str, float],
        nearest_dirt_distance: float | None,
    ):
        return {
            "steps": int(self.steps),
            "hit_wall": hit_wall,
            "hit_obstacle": hit_obstacle,
            "found_dirt": found_dirt,
            "success": found_dirt,
            "cleaned_count": int(found_dirt),
            "remaining_dirt": int(len(self.dirt)),
            "nearest_dirt_distance": nearest_dirt_distance,
            "reward_components": reward_components,
        }

    @staticmethod
    def _empty_reward_components():
        return {
            "step_penalty": -0.01,
            "dirt_visible": 0.0,
            "dirt_progress": 0.0,
            "found_dirt": 0.0,
            "wall_penalty": 0.0,
            "obstacle_penalty": 0.0,
        }

    @staticmethod
    def _normalize_heading(heading):
        return float(((heading + np.pi) % (2 * np.pi)) - np.pi)

    def _hits_obstacle(self, point):
        for obstacle in self.obstacles:
            center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
            if np.linalg.norm(point - center) <= obstacle.radius:
                return True
        return False

    def render(self):
        return None

    def close(self):
        return None
