import numpy as np
from grid import Air, GridLayer, Rubble, Stone, Wall
from grid import Np2dArray
from typing import Dict, List

from dataclasses import dataclass

@dataclass
class Room:
    xmin: int
    ymin: int
    ymax: int
    xmax: int


def generate_rooms(width: int, height: int, num_rooms: int, room_min: int, room_max: int) -> List[Room]:
    """
    Generate a list of rooms which may overlap but which may not extend outside the boundaries of the map.
    """
    rooms: List[Room] = []

    def saturate_x_coord(c):
        return max(0, min(width, c))

    def saturate_y_coord(c):
        return max(0, min(width, c))

    tries = 0
    while len(rooms) < num_rooms and tries < num_rooms*2:
        room_x = np.random.randint(width)
        room_y = np.random.randint(height)
        room_width = np.random.randint(room_min, room_max+1)
        room_height = np.random.randint(room_min, room_max+1)

        if room_x+room_width >= width or room_y+room_height >= height:
            continue

        rooms.append(Room(
            xmin=room_x,
            xmax=room_x+room_width,
            ymin=room_y,
            ymax=room_y+room_height,
        ))
    return rooms


def num_rooms_per_tile(width: int, height: int, rooms: List[Room]) -> Np2dArray[int]:
    number_of_rooms = np.zeros(shape=(width, height), dtype=int)
    for room in rooms:
        xs = np.arange(room.xmin, room.xmax+1)
        ys = np.arange(room.ymin, room.ymax+1)
        number_of_rooms[np.ix_(xs, ys)] += 1
    return number_of_rooms


def wall_tiles_mask(width: int, height: int, rooms: List[Room]) -> Np2dArray[bool]:
    wall_tiles = np.full((width, height), False)
    for room in rooms:
        xrange = np.arange(room.xmin, room.xmax+1)
        yrange = np.arange(room.ymin, room.ymax+1)
        xmin = np.asarray([room.xmin])
        xmax = np.asarray([room.xmax])
        ymin = np.asarray([room.ymin])
        ymax = np.asarray([room.ymax])
        wall_tiles[np.ix_(xrange, ymin)] = True
        wall_tiles[np.ix_(xrange, ymax)] = True
        wall_tiles[np.ix_(xmin, yrange)] = True
        wall_tiles[np.ix_(xmax, yrange)] = True
    return wall_tiles


def rubble_mask(width: int, height: int) -> Np2dArray[bool]:
    area = width * height
    number_of_rubble_tiles = area//9
    result = np.full((width, height), False)
    for _ in range(number_of_rubble_tiles):
        result[np.random.randint(width), np.random.randint(height)] = True
    return result


def generate_dungeon(width: int,
                     height: int,
                     num_rooms: int,
                     room_min: int,
                     room_max: int) -> Dict[GridLayer, Np2dArray[int]]:
    # Generate n rooms (which may overlap)
    rooms: List[Room] = generate_rooms(width, height, num_rooms, room_min, room_max)

    # We need to only add walls where rooms do not overlap. So, keep track of # of rooms for each tile
    number_of_rooms = num_rooms_per_tile(width, height, rooms)
    # And get wall tiles of each room
    wall_tiles = wall_tiles_mask(width, height, rooms)
    # Add random rubble tiles
    rubble_tiles = rubble_mask(width, height)

    results = {}
    results[Stone] = (number_of_rooms == 0).astype(int)
    results[Wall] = ((number_of_rooms == 1) & wall_tiles).astype(int)
    results[Air] = ((number_of_rooms > 0) & np.logical_not((number_of_rooms == 1) & wall_tiles)).astype(int)
    results[Rubble] = (rubble_tiles & ((number_of_rooms > 0) & np.logical_not((number_of_rooms == 1) & wall_tiles))).astype(int)
    return results


if __name__ == '__main__':
    results = generate_dungeon(50, 50, 5, 5, 20)
    print(results)
