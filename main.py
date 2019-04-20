from typing import Any

from grid import GridManager

from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

from events import Client, Event, EventManager, Service, ServiceResult, Subscriber


class PlayerMoveEvent(Event):
    def __init__(self, direction):
        self.direction = direction
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4


class PushObjectService(Service):
    def __init__(self, x: int, y: int, dx: int, dy: int):
        super().__init__(ServiceResult)
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def print(self, screen) -> None:
        screen.print_at('@', self.x, self.y)


class PlayerMover(Subscriber):
    def __init__(self, event_manager: EventManager, player: Player, grid_manager: GridManager):
        self.event_manager = event_manager
        self.player = player
        self.grid_manager = grid_manager
        event_manager.subscribe(PlayerMoveEvent, self)

    def handle_event(self, event: PlayerMoveEvent) -> None:
        ds = {
            PlayerMoveEvent.UP: (0, -1),
            PlayerMoveEvent.LEFT: (-1, 0),
            PlayerMoveEvent.DOWN: (0, 1),
            PlayerMoveEvent.RIGHT: (1, 0),
        }
        dx, dy = ds[event.direction]
        x_target, y_target = self.player.x + dx, self.player.y + dy
        if not self.grid_manager.is_within_bounds(x_target, y_target):
            return

        # Keep trying actions until one succeeds
        actions = [self.attempt_move_through, self.attempt_push]
        for action in actions:
            if action(x_target, y_target):
                break

    def attempt_move_through(self, x_target, y_target) -> bool:
        if self.grid_manager.tile_is_any(x_target, y_target, can_move_through=False):
            return False
        self.player.x = x_target
        self.player.y = y_target
        return True

    def attempt_push(self, x_target, y_target) -> bool:
        print('Attempting to push object.')
        result = self.event_manager.service(PushObjectService(
            x=x_target,
            y=y_target,
            dx=x_target-self.player.x,
            dy=y_target-self.player.y,
        ))
        if result == ServiceResult.Success:
            if self.grid_manager.tile_is_all(x_target, y_target, can_move_through=True):
                self.player.x = x_target
                self.player.y = y_target
            return True
        return False


class InteractionHandler(Client):
    def __init__(self, event_manager: EventManager, grid_manager: GridManager):
        self.event_manager = event_manager
        self.grid_manager = grid_manager
        self.event_manager.client(PushObjectService, self)

    def handle_service(self, service: Service) -> Any:
        handlers = {
            PushObjectService: self.handle_push,
        }
        return handlers[type(service)](service)

    def handle_push(self, service: PushObjectService) -> ServiceResult:
        # In order to properly push an object, we need
        #  - a line of tiles where in each tile every layer is either pushable or move-throughable
        #  - at the end, a tile where every object is move-throughable

        # HACK: don't want to deal with moving with large dx or dy, or with not moving at all
        assert abs(service.dx) in [0, 1]
        assert abs(service.dy) in [0, 1]
        assert abs(service.x) + abs(service.y) > 0

        x = service.x
        y = service.y

        if not self.grid_manager.tile_is_any(x, y, pushable=True):
            # There is not actually a pushable layer in the tile being pushed
            return ServiceResult.Failure

        # Make sure everything can be pushed properly
        while True:
            x += service.dx
            y += service.dy
            if self.grid_manager.tile_is_all(x, y, can_move_through=True):
                # Found a valid destination tile. Everything can be properly pushed.
                break
            elif not self.grid_manager.tile_is_any(x, y, can_move_through=False, pushable=False):
                # Found a tile where things can be pushed through but cannot work as the final tile
                pass
            else:
                # An object runs into something that cannot be pushed aside
                return ServiceResult.Failure

        # By now, (x, y) are the coordinates of the final tile (things are pushed into, but not out of, this tile).
        # Do the actual pushing.

        while True:
            x -= service.dx
            y -= service.dy
            # HACK
            for layer, density in self.grid_manager.layers.items():
                if not layer.pushable or density[x, y] == 0:
                    continue
                density[x, y] = 0
                density[x + service.dx, y + service.dy] = 1
            if x == service.x and y == service.y:
                break

        return ServiceResult.Success


def main(screen):
    grid_manager = GridManager()
    player = Player(*grid_manager.random_move_through_tile())
    event_manager = EventManager()
    player_mover = PlayerMover(event_manager, player, grid_manager)  # noqa: F841
    interaction_handler = InteractionHandler(event_manager, grid_manager)  # noqa: F841

    while True:
        grid_manager.print(screen)
        player.print(screen)
        screen.refresh()
        event = screen.get_event()
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_UP:
                event_manager.publish(PlayerMoveEvent(PlayerMoveEvent.UP))
            elif event.key_code == Screen.KEY_LEFT:
                event_manager.publish(PlayerMoveEvent(PlayerMoveEvent.LEFT))
            elif event.key_code == Screen.KEY_DOWN:
                event_manager.publish(PlayerMoveEvent(PlayerMoveEvent.DOWN))
            elif event.key_code == Screen.KEY_RIGHT:
                event_manager.publish(PlayerMoveEvent(PlayerMoveEvent.RIGHT))


if __name__ == '__main__':
    Screen.wrapper(main)
