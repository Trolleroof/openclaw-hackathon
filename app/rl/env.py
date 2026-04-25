import gymnasium as gym
from gymnasium import spaces
import numpy as np


class RoombaEnv(gym.Env):
    """
    Tiny Roomba-style cleaning environment.

    The robot is a point/circle in a 2D room.

    Observation:
        Normalized navigation features: robot pose, nearest dirt geometry,
        wall distances, remaining dirt, and up to three nearest dirt vectors.

    Actions:
        0 = move forward
        1 = turn left
        2 = turn right
    """

    metadata = {"render_modes": ["human", "rgb_array"]}
    observation_size = 23
    max_observed_dirt = 3

    def __init__(
        self,
        room_size: float = 10.0,
        max_steps: int = 200,
        dirt_count: int = 3,
        clean_radius: float = 0.5,
        forward_step: float = 0.3,
        turn_angle: float = 0.3,
        seed: int | None = None,
        render_mode: str | None = None,
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

        self.action_space = spaces.Discrete(3)

        high = np.ones(self.observation_size, dtype=np.float32)
        low = -np.ones(self.observation_size, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self.rng = np.random.default_rng(seed)
        self.robot = None
        self.heading = None
        self.dirt = None
        self.steps = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if seed is not None:
            self.rng = np.random.default_rng(seed)

        self.robot = np.array([1.0, 1.0], dtype=np.float32)
        self.heading = 0.0
        self.steps = 0

        self.dirt = self._generate_dirt()

        return self._obs(), {}

    def _generate_dirt(self):
        presets = np.array(
            [
                [8.0, 8.0],
                [2.0, 7.0],
                [7.0, 2.0],
                [5.0, 5.0],
                [8.0, 3.0],
                [3.0, 8.0],
            ],
            dtype=np.float32,
        )

        if self.dirt_count <= len(presets):
            dirt = presets[: self.dirt_count].copy()
            dirt = np.clip(dirt, 0.5, self.size - 0.5)
            return dirt.astype(np.float32)

        extra = self.rng.uniform(0.5, self.size - 0.5, size=(self.dirt_count, 2))
        return extra.astype(np.float32)

    def _obs(self):
        nearest, nearest_distance = self._nearest_dirt()
        heading_error = self._heading_error_to(nearest)

        dirt_features = []
        if len(self.dirt) > 0:
            distances = np.linalg.norm(self.dirt - self.robot, axis=1)
            dirt_vectors = self.dirt[np.argsort(distances)] - self.robot
        else:
            dirt_vectors = np.empty((0, 2), dtype=np.float32)

        for index in range(self.max_observed_dirt):
            if index < len(dirt_vectors):
                vector = np.clip(dirt_vectors[index] / self.size, -1.0, 1.0)
                dirt_features.extend([vector[0], vector[1], 1.0])
            else:
                dirt_features.extend([0.0, 0.0, 0.0])

        return np.array(
            [
                self.robot[0] / self.size,
                self.robot[1] / self.size,
                np.sin(self.heading),
                np.cos(self.heading),
                nearest[0] / self.size,
                nearest[1] / self.size,
                nearest_distance / (self.size * np.sqrt(2.0)),
                np.sin(heading_error),
                np.cos(heading_error),
                len(self.dirt) / max(self.dirt_count, 1),
                self.robot[0] / self.size,
                (self.size - self.robot[0]) / self.size,
                self.robot[1] / self.size,
                (self.size - self.robot[1]) / self.size,
                *dirt_features,
            ],
            dtype=np.float32,
        )

    def _nearest_dirt(self):
        if len(self.dirt) == 0:
            return np.array([0.0, 0.0], dtype=np.float32), 0.0

        vectors = self.dirt - self.robot
        distances = np.linalg.norm(vectors, axis=1)
        nearest_index = int(np.argmin(distances))
        return vectors[nearest_index].astype(np.float32), float(distances[nearest_index])

    def _nearest_dirt_distance(self):
        return self._nearest_dirt()[1]

    def _heading_error_to(self, vector):
        if np.allclose(vector, 0.0):
            return 0.0
        target_angle = float(np.arctan2(vector[1], vector[0]))
        return float(((target_angle - self.heading + np.pi) % (2 * np.pi)) - np.pi)

    def step(self, action):
        self.steps += 1
        reward_components = {
            "step_penalty": -0.01,
            "turn_penalty": 0.0,
            "wall_penalty": 0.0,
            "progress": 0.0,
            "alignment": 0.0,
            "clean": 0.0,
            "terminal": 0.0,
        }
        previous_nearest, previous_nearest_distance = self._nearest_dirt()
        previous_heading_error = abs(self._heading_error_to(previous_nearest))

        if action == 0:
            direction = np.array(
                [np.cos(self.heading), np.sin(self.heading)],
                dtype=np.float32,
            )
            self.robot += direction * self.forward_step
        elif action == 1:
            self.heading += self.turn_angle
            reward_components["turn_penalty"] = -0.002
        elif action == 2:
            self.heading -= self.turn_angle
            reward_components["turn_penalty"] = -0.002

        self.heading = ((self.heading + np.pi) % (2 * np.pi)) - np.pi

        hit_wall = bool(np.any(self.robot < 0.0) or np.any(self.robot > self.size))
        if hit_wall:
            self.robot = np.clip(self.robot, 0.0, self.size)
            reward_components["wall_penalty"] = -1.5

        cleaned_count = 0
        nearest_dirt_distance = 0.0
        heading_error = 0.0
        if len(self.dirt) > 0:
            distances = np.linalg.norm(self.dirt - self.robot, axis=1)
            nearest_dirt_distance = float(np.min(distances))
            nearest = self.dirt[int(np.argmin(distances))] - self.robot
            heading_error = abs(self._heading_error_to(nearest))

            reward_components["progress"] = (previous_nearest_distance - nearest_dirt_distance) * 0.8
            reward_components["alignment"] = (previous_heading_error - heading_error) * 0.1

            cleaned = distances < self.clean_radius
            cleaned_count = int(np.sum(cleaned))
            reward_components["clean"] = float(cleaned_count) * 5.0
            self.dirt = self.dirt[~cleaned]

        terminated = len(self.dirt) == 0
        truncated = self.steps >= self.max_steps

        if terminated:
            reward_components["terminal"] = 15.0
            reward_components["terminal"] += 5.0 * ((self.max_steps - self.steps) / self.max_steps)

        reward = float(sum(reward_components.values()))

        info = {
            "remaining_dirt": int(len(self.dirt)),
            "steps": int(self.steps),
            "hit_wall": hit_wall,
            "cleaned_count": cleaned_count,
            "nearest_dirt_distance": nearest_dirt_distance,
            "heading_error": heading_error,
            "reward_components": reward_components,
        }

        return self._obs(), reward, terminated, truncated, info

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

        for dirt in self.dirt:
            center = world_to_pixel(dirt)
            self._draw_disc(image, center, radius=7, color=np.array([139, 90, 43], dtype=np.uint8))

        robot_center = world_to_pixel(self.robot)
        self._draw_disc(image, robot_center, radius=10, color=np.array([40, 110, 220], dtype=np.uint8))

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
            color=np.array([10, 40, 90], dtype=np.uint8),
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
