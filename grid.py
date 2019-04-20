import numpy as np
from abc import ABC, abstractmethod
from typing import _alias, T, Tuple, Union

Np2dArray = _alias(np.ndarray, T, inst=False)


class GridLayer(ABC):
    def __init__(self, can_move_through: bool = False, pushable: bool = False):
        self.can_move_through = can_move_through
        self.pushable = pushable

    layers = []

    @abstractmethod
    def show(self, density: Np2dArray[int]) -> Np2dArray[str]:
        pass


class GridManager:
    def __init__(self):
        layer_types = [Layer() for Layer in GridLayer.layers]
        self.width = 100
        self.height = 10
        from dungeon_generator import generate_dungeon
        dungeon_res = generate_dungeon(self.width, self.height, num_rooms=5, room_min=5, room_max=20)
        self.layers = {Layer(): density for Layer, density in dungeon_res.items()}
        # self.layers = {l: np.random.randint(0, 2, size=(self.width, self.height)) for l in layer_types}

    def print(self, screen) -> None:
        results = np.full(shape=(self.width, self.height), fill_value=' ', dtype=str)

        for layer, density in self.layers.items():
            results = np.where(
                density == 1,
                layer.show(density),
                results,
            )
        # for y in range(self.height):
        #     for x in range(self.width):
        #         print(results[x, y], end='')
        #     print()
        for y in range(self.height):
            screen.print_at(''.join(results[:, y]), 0, y)
    
    def is_within_bounds(self, x: int, y: int) -> bool:
        return x >= 0 and x < self.width and y >= 0 and y < self.height

    def tile_is_any(self, x: int, y: int, **kwargs) -> bool:
        for layer, density in self.layers.items():
            if density[x, y] != 1:
                continue
            if all(getattr(layer, name) == value for name, value in kwargs.items()):
                return True
        return False

    def tile_is_all(self, x: int, y: int, **kwargs) -> bool:
        for layer, density in self.layers.items():
            if density[x, y] != 1:
                continue
            if any(getattr(layer, name) != value for name, value in kwargs.items()):
                return False
        return True

    def random_move_through_tile(self) -> Tuple[int, int]:
        while True:
            x = np.random.randint(self.width)
            y = np.random.randint(self.height)
            found = True
            for layer, density in self.layers.items():
                if not layer.can_move_through and density[x, y] == 1:
                    found = False
                    break
            if found:
                return x, y


class Stone(GridLayer):
    def __init__(self):
        super().__init__()

    def show(self, density: Np2dArray[int]) -> Np2dArray[str]:
        return np.where(density == 1, ' ', ' ')  # ▮
GridLayer.layers.append(Stone)


class Wall(GridLayer):
    def __init__(self):
        super().__init__()

    def show(self, density: Np2dArray[int]) -> Np2dArray[str]:
        return np.full_like(density, '#', dtype=str)
GridLayer.layers.append(Wall)


class Air(GridLayer):
    def __init__(self):
        super().__init__(can_move_through=True)

    def show(self, density: Np2dArray[int]) -> Np2dArray[str]:
        return np.where(density == 1, '·', ' ')
GridLayer.layers.append(Air)


class Rubble(GridLayer):
    def __init__(self):
        super().__init__(pushable=True)

    def show(self, density: Np2dArray[int]) -> Np2dArray[str]:
        return np.where(density == 1, '0', ' ')  # ◈
GridLayer.layers.append(Rubble)

