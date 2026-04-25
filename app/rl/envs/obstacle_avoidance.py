from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from app.rl.layouts import CircleObstacle, LayoutConfig, generate_layout
from app.rl.sensors import cast_lidar_rays


class ObstacleAvoidanceEnv(gym.Env):
    """ClawLab curriculum env focused only on collision-free navigation."""

    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(
        self,
        room_size: float = 10.0,
        max_steps: int = 200,
        obstacle_count: int = 6,
        forward_step: float = 0.3,
        turn_angle: float = 0.3,
        lidar_rays: int = 16,
        lidar_range: float | None = None,
        min_clearance: float = 0.8,
        min_success_path_length: float | None = None,
        safe_waypoint: tuple[float, float] | None = None,
        waypoint_radius: float = 0.5,
        seed: int | None = None,
        render_mode: str | None = None,
    ):
        super().__init__()

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"Unsupported render_mode: {render_mode}")
        if lidar_rays <= 0:
            raise ValueError("lidar_rays must be positive")

        self.size = float(room_size)
        self.max_steps = int(max_steps)
        self.obstacle_count = int(obstacle_count)
        self.forward_step = float(forward_step)
        self.turn_angle = float(turn_angle)
        self.lidar_rays = int(lidar_rays)
        self.lidar_range = float(lidar_range or room_size)
        self.min_clearance = float(min_clearance)
        self.min_success_path_length = float(min_success_path_length or room_size * 0.75)
        self.safe_waypoint = (
            np.array(safe_waypoint, dtype=np.float32)
            if safe_waypoint is not None
            else None
        )
        self.waypoint_radius = float(waypoint_radius)
        self.render_mode = render_mode

        self.action_space = spaces.Discrete(3)
        observation_size = 2 + self.lidar_rays + 4
        self.observation_space = spaces.Box(
            low=-np.ones(observation_size, dtype=np.float32),
            high=np.ones(observation_size, dtype=np.float32),
            dtype=np.float32,
        )

        self.rng = np.random.default_rng(seed)
        self.robot = np.zeros(2, dtype=np.float32)
        self.heading = 0.0
        self.obstacles: list[CircleObstacle] = []
        self.steps = 0
        self.path_length = 0.0

        self.dirt_count = 0
        self.dirt = np.empty((0, 2), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if seed is not None:
            self.rng = np.random.default_rng(seed)

        layout_seed = seed
        if layout_seed is None:
            layout_seed = int(self.rng.integers(0, np.iinfo(np.int32).max))

        layout = generate_layout(
            LayoutConfig(
                mode="random",
                room_size=self.size,
                dirt_count=0,
                obstacle_count=self.obstacle_count,
                min_clearance=self.min_clearance,
                randomize_start=True,
            ),
            seed=layout_seed,
        )

        self.robot = layout.robot.copy()
        self.heading = float(layout.heading)
        self.obstacles = list(layout.obstacles)
        self.steps = 0
        self.path_length = 0.0
        self.dirt = np.empty((0, 2), dtype=np.float32)

        return self._obs(), self._info(
            hit_wall=False,
            hit_obstacle=False,
            reward_components=self._empty_reward_components(),
        )

    def step(self, action):
        self.steps += 1
        action = int(action)
        previous_robot = self.robot.copy()
        reward_components = self._empty_reward_components()
        reward_components["step_penalty"] = -0.01

        hit_wall = False
        hit_obstacle = False

        if action == 0:
            direction = np.array(
                [np.cos(self.heading), np.sin(self.heading)],
                dtype=np.float32,
            )
            proposed_robot = self.robot + direction * self.forward_step
            hit_wall = self._hits_wall(proposed_robot)
            hit_obstacle = self._hits_obstacle(proposed_robot)
            if hit_wall or hit_obstacle:
                self.robot = previous_robot
            else:
                self.robot = proposed_robot.astype(np.float32)
                self.path_length += float(np.linalg.norm(self.robot - previous_robot))
                reward_components["forward_reward"] = 0.05
        elif action == 1:
            self.heading += self.turn_angle
        elif action == 2:
            self.heading -= self.turn_angle
        else:
            raise ValueError(f"Unsupported action: {action}")

        self.heading = self._normalize_heading(self.heading)

        if hit_wall:
            reward_components["wall_penalty"] = -3.0
        if hit_obstacle:
            reward_components["obstacle_penalty"] = -5.0

        clearance = self._min_clearance()
        reward_components["clearance_reward"] = 0.03 * clearance

        reached_waypoint = self._reached_safe_waypoint()
        survived = self.steps >= self.max_steps
        terminated = bool(survived or reached_waypoint)
        success = bool(
            reached_waypoint
            or (survived and self.path_length >= self.min_success_path_length)
        )
        truncated = False
        if success:
            reward_components["survival_bonus"] = 1.0
        elif survived:
            reward_components["idle_penalty"] = -2.0

        reward = float(sum(reward_components.values()))
        info = self._info(
            hit_wall=hit_wall,
            hit_obstacle=hit_obstacle,
            reward_components=reward_components,
            reached_waypoint=reached_waypoint,
            success=success,
        )
        return self._obs(), reward, terminated, truncated, info

    def _obs(self):
        lidar = cast_lidar_rays(
            robot=self.robot,
            heading=self.heading,
            room_size=self.size,
            obstacles=self.obstacles,
            ray_count=self.lidar_rays,
            max_range=self.lidar_range,
        )
        wall_clearances = np.array(
            [
                self.robot[0] / self.size,
                (self.size - self.robot[0]) / self.size,
                self.robot[1] / self.size,
                (self.size - self.robot[1]) / self.size,
            ],
            dtype=np.float32,
        )
        obs = np.array(
            [
                np.sin(self.heading),
                np.cos(self.heading),
                *lidar,
                *wall_clearances,
            ],
            dtype=np.float32,
        )
        return np.clip(obs, -1.0, 1.0).astype(np.float32)

    def _info(
        self,
        hit_wall: bool,
        hit_obstacle: bool,
        reward_components: dict[str, float],
        reached_waypoint: bool = False,
        success: bool = False,
    ):
        return {
            "remaining_dirt": 0,
            "steps": int(self.steps),
            "hit_wall": bool(hit_wall),
            "hit_obstacle": bool(hit_obstacle),
            "success": bool(success),
            "cleaned_count": 0,
            "nearest_dirt_distance": 0.0,
            "heading_error": 0.0,
            "reached_waypoint": bool(reached_waypoint),
            "min_clearance": self._min_clearance(),
            "path_length": float(self.path_length),
            "reward_components": reward_components,
        }

    @staticmethod
    def _empty_reward_components():
        return {
            "step_penalty": 0.0,
            "forward_reward": 0.0,
            "clearance_reward": 0.0,
            "wall_penalty": 0.0,
            "obstacle_penalty": 0.0,
            "survival_bonus": 0.0,
            "idle_penalty": 0.0,
        }

    @staticmethod
    def _normalize_heading(heading: float) -> float:
        return float(((heading + np.pi) % (2 * np.pi)) - np.pi)

    def _hits_wall(self, point: np.ndarray) -> bool:
        return bool(
            point[0] <= 0.0
            or point[0] >= self.size
            or point[1] <= 0.0
            or point[1] >= self.size
        )

    def _hits_obstacle(self, point: np.ndarray) -> bool:
        for obstacle in self.obstacles:
            center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
            if np.linalg.norm(point - center) <= obstacle.radius:
                return True
        return False

    def _min_clearance(self) -> float:
        lidar = cast_lidar_rays(
            robot=self.robot,
            heading=self.heading,
            room_size=self.size,
            obstacles=self.obstacles,
            ray_count=self.lidar_rays,
            max_range=self.lidar_range,
        )
        return float(np.clip(np.min(lidar), 0.0, 1.0))

    def _reached_safe_waypoint(self) -> bool:
        if self.safe_waypoint is None:
            return False
        return bool(np.linalg.norm(self.robot - self.safe_waypoint) <= self.waypoint_radius)

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

        def world_to_pixel(point):
            x = margin + int((float(point[0]) / self.size) * arena_size)
            y = image_size - margin - int((float(point[1]) / self.size) * arena_size)
            return np.array([np.clip(x, 0, image_size - 1), np.clip(y, 0, image_size - 1)])

        for obstacle in self.obstacles:
            center = world_to_pixel(np.array([obstacle.x, obstacle.y], dtype=np.float32))
            radius = max(2, int((obstacle.radius / self.size) * arena_size))
            self._draw_disc(image, center, radius, np.array([90, 90, 90], dtype=np.uint8))

        robot_center = world_to_pixel(self.robot)
        self._draw_disc(image, robot_center, 10, np.array([40, 110, 220], dtype=np.uint8))
        heading_end = robot_center + np.array(
            [
                int(np.cos(self.heading) * 18),
                -int(np.sin(self.heading) * 18),
            ]
        )
        self._draw_line(
            image,
            robot_center,
            np.clip(heading_end, 0, image_size - 1),
            np.array([10, 40, 90], dtype=np.uint8),
        )
        return image

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

    @staticmethod
    def _draw_line(image, start, end, color):
        points = max(abs(int(end[0]) - int(start[0])), abs(int(end[1]) - int(start[1])), 1)
        xs = np.linspace(int(start[0]), int(end[0]), points + 1).astype(int)
        ys = np.linspace(int(start[1]), int(end[1]), points + 1).astype(int)
        image[ys, xs] = color

    def close(self):
        return None
