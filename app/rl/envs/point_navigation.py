from __future__ import annotations

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from app.rl.layouts import CircleObstacle, LayoutConfig, generate_layout
from app.rl.sensors import cast_lidar_rays


class PointNavigationEnv(gym.Env):
    """Point-goal navigation environment for the ClawLab curriculum."""

    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(
        self,
        room_size: float = 10.0,
        max_steps: int = 200,
        forward_step: float = 0.3,
        turn_angle: float = 0.3,
        target_radius: float = 0.4,
        obstacle_count: int = 0,
        lidar_rays: int = 8,
        layout_mode: str = "random",
        seed: int | None = None,
        render_mode: str | None = None,
        min_clearance: float = 0.8,
    ):
        super().__init__()

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"Unsupported render_mode: {render_mode}")

        self.size = float(room_size)
        self.max_steps = int(max_steps)
        self.forward_step = float(forward_step)
        self.turn_angle = float(turn_angle)
        self.target_radius = float(target_radius)
        self.obstacle_count = int(obstacle_count)
        self.lidar_rays = int(lidar_rays)
        self.layout_mode = layout_mode
        self.render_mode = render_mode
        self.min_clearance = float(min_clearance)
        self.max_target_distance = self.size * np.sqrt(2.0)

        self.action_space = spaces.Discrete(3)
        observation_size = 6 + self.lidar_rays
        self.observation_space = spaces.Box(
            low=-np.ones(observation_size, dtype=np.float32),
            high=np.ones(observation_size, dtype=np.float32),
            dtype=np.float32,
        )

        self.rng = np.random.default_rng(seed)
        self.robot = np.zeros(2, dtype=np.float32)
        self.heading = 0.0
        self.target = np.zeros(2, dtype=np.float32)
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
                dirt_count=0,
                obstacle_count=self.obstacle_count,
                min_clearance=self.min_clearance,
            ),
            seed=layout_seed,
        )

        self.robot = layout.robot.copy()
        self.heading = float(layout.heading)
        self.obstacles = list(layout.obstacles)
        self.target = self._sample_target()
        self.steps = 0

        return self._obs(), self._info(
            hit_wall=False,
            hit_obstacle=False,
            reward_components=self._empty_reward_components(),
        )

    def step(self, action):
        self.steps += 1
        previous_robot = self.robot.copy()
        previous_distance = self._target_distance()
        previous_heading_error = abs(self._heading_error_to_target())

        reward_components = self._empty_reward_components()

        if action == 0:
            direction = np.array(
                [np.cos(self.heading), np.sin(self.heading)],
                dtype=np.float32,
            )
            self.robot = self.robot + (direction * self.forward_step)
        elif action == 1:
            self.heading += self.turn_angle
            reward_components["turn_penalty"] = -0.01
        elif action == 2:
            self.heading -= self.turn_angle
            reward_components["turn_penalty"] = -0.01

        self.heading = self._normalize_heading(self.heading)

        hit_wall = self._hits_wall(self.robot)
        if hit_wall:
            self.robot = previous_robot
            reward_components["wall_penalty"] = -3.0

        hit_obstacle = self._hits_obstacle(self.robot)
        if hit_obstacle:
            self.robot = previous_robot
            reward_components["obstacle_penalty"] = -4.0

        target_distance = self._target_distance()
        heading_error = abs(self._heading_error_to_target())

        reward_components["progress"] = (previous_distance - target_distance) * 1.5
        reward_components["alignment"] = (previous_heading_error - heading_error) * 0.1

        success = target_distance <= self.target_radius
        terminated = bool(success)
        truncated = self.steps >= self.max_steps

        if success:
            reward_components["success"] = 10.0 + 2.0 * (
                (self.max_steps - self.steps) / max(self.max_steps, 1)
            )

        reward = float(sum(reward_components.values()))
        info = self._info(
            hit_wall=hit_wall,
            hit_obstacle=hit_obstacle,
            reward_components=reward_components,
            success=success,
            target_distance=target_distance,
            heading_error=heading_error,
        )

        return self._obs(), reward, terminated, truncated, info

    def _obs(self):
        target_vector = self.target - self.robot
        target_forward = (
            float(target_vector[0]) * np.cos(self.heading)
            + float(target_vector[1]) * np.sin(self.heading)
        )
        target_left = (
            -float(target_vector[0]) * np.sin(self.heading)
            + float(target_vector[1]) * np.cos(self.heading)
        )
        target_distance = self._target_distance()
        lidar = cast_lidar_rays(
            robot=self.robot,
            heading=self.heading,
            room_size=self.size,
            obstacles=self.obstacles,
            ray_count=self.lidar_rays,
            max_range=self.size,
        )
        remaining_step_fraction = 1.0 - (self.steps / max(self.max_steps, 1))

        return np.array(
            [
                np.sin(self.heading),
                np.cos(self.heading),
                np.clip(target_forward / self.size, -1.0, 1.0),
                np.clip(target_left / self.size, -1.0, 1.0),
                np.clip(target_distance / self.max_target_distance, 0.0, 1.0),
                *lidar,
                np.clip(remaining_step_fraction, 0.0, 1.0),
            ],
            dtype=np.float32,
        )

    def render(self):
        if self.render_mode is None:
            return None

        image_size = 400
        image = np.full((image_size, image_size, 3), 245, dtype=np.uint8)
        margin = 20
        arena_size = image_size - (margin * 2)
        image[margin : image_size - margin, margin : image_size - margin] = np.array(
            [255, 255, 255],
            dtype=np.uint8,
        )

        for obstacle in self.obstacles:
            center = self._world_to_pixel(
                np.array([obstacle.x, obstacle.y], dtype=np.float32),
                image_size,
                margin,
            )
            radius = max(2, int((obstacle.radius / self.size) * arena_size))
            self._draw_disc(
                image,
                center,
                radius=radius,
                color=np.array([90, 90, 90], dtype=np.uint8),
            )

        self._draw_disc(
            image,
            self._world_to_pixel(self.target, image_size, margin),
            radius=max(4, int((self.target_radius / self.size) * arena_size)),
            color=np.array([40, 180, 100], dtype=np.uint8),
        )
        self._draw_disc(
            image,
            self._world_to_pixel(self.robot, image_size, margin),
            radius=8,
            color=np.array([40, 110, 220], dtype=np.uint8),
        )
        return image

    def close(self):
        return None

    def _sample_target(self) -> np.ndarray:
        for _ in range(500):
            point = self.rng.uniform(0.5, self.size - 0.5, size=2).astype(np.float32)
            if np.linalg.norm(point - self.robot) < self.target_radius + self.min_clearance:
                continue
            if self._hits_obstacle(point):
                continue
            return point
        raise RuntimeError("Could not sample target with requested clearance")

    def _target_distance(self) -> float:
        return float(np.linalg.norm(self.target - self.robot))

    def _heading_error_to_target(self) -> float:
        vector = self.target - self.robot
        if np.allclose(vector, 0.0):
            return 0.0
        target_angle = float(np.arctan2(vector[1], vector[0]))
        return self._normalize_heading(target_angle - self.heading)

    def _hits_wall(self, point: np.ndarray) -> bool:
        return bool(np.any(point < 0.0) or np.any(point > self.size))

    def _hits_obstacle(self, point: np.ndarray) -> bool:
        for obstacle in self.obstacles:
            center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
            if np.linalg.norm(point - center) <= obstacle.radius:
                return True
        return False

    def _info(
        self,
        hit_wall: bool,
        hit_obstacle: bool,
        reward_components: dict[str, float],
        success: bool = False,
        target_distance: float | None = None,
        heading_error: float | None = None,
    ) -> dict:
        return {
            "steps": int(self.steps),
            "target": self.target.copy(),
            "target_distance": self._target_distance()
            if target_distance is None
            else float(target_distance),
            "heading_error": abs(self._heading_error_to_target())
            if heading_error is None
            else float(heading_error),
            "hit_wall": bool(hit_wall),
            "hit_obstacle": bool(hit_obstacle),
            "success": bool(success),
            "reward_components": reward_components,
        }

    @staticmethod
    def _empty_reward_components() -> dict[str, float]:
        return {
            "step_penalty": -0.01,
            "progress": 0.0,
            "alignment": 0.0,
            "turn_penalty": 0.0,
            "wall_penalty": 0.0,
            "obstacle_penalty": 0.0,
            "success": 0.0,
        }

    @staticmethod
    def _normalize_heading(angle: float) -> float:
        return float(((angle + np.pi) % (2 * np.pi)) - np.pi)

    def _world_to_pixel(self, point, image_size, margin):
        arena_size = image_size - (margin * 2)
        x = margin + int((float(point[0]) / self.size) * arena_size)
        y = image_size - margin - int((float(point[1]) / self.size) * arena_size)
        return np.array(
            [np.clip(x, 0, image_size - 1), np.clip(y, 0, image_size - 1)]
        )

    @staticmethod
    def _draw_disc(image, center, radius, color):
        height, width = image.shape[:2]
        x_min = max(int(center[0]) - radius, 0)
        x_max = min(int(center[0]) + radius + 1, width)
        y_min = max(int(center[1]) - radius, 0)
        y_max = min(int(center[1]) + radius + 1, height)

        yy, xx = np.ogrid[y_min:y_max, x_min:x_max]
        mask = (xx - int(center[0])) ** 2 + (yy - int(center[1])) ** 2 <= radius**2
        image[y_min:y_max, x_min:x_max][mask] = color
