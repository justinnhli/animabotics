"""The abstract Game class."""

from time import monotonic_ns as get_nsec_msec
from typing import Callable

from .camera import Camera
from .canvas import Canvas, Input, EventCallback
from .game_object import GameObject
from .scene import HierarchicalHashGrid


CollisionCallback = Callable[[GameObject, GameObject], None]


class Game:
    """A game."""

    def __init__(self, window_width, window_height):
        # type: (int, int) -> None
        """Initialize the Game."""
        self.window_width = window_width
        self.window_height = window_height
        # components
        self.canvas = Canvas(window_width, window_height)
        self.camera = Camera(self.canvas)
        # objects
        self.scene = HierarchicalHashGrid()
        self.collision_callbacks = {} # type: dict[tuple[str, str], CollisionCallback]
        # settings
        self.keybinds = {} # type: dict[Input, EventCallback]
        # state
        self.prev_msec = None # type: int

    def add_object(self, game_object):
        # type: (GameObject) -> None
        """Add an object to the scene."""
        self.scene.add(game_object)

    def bind(self, input_event, callback):
        # type: (Input, EventCallback) -> None
        """Add a keybind."""
        self.keybinds[input_event] = callback

    def on_collision(self, group1, group2, callback):
        # type: (str, str, CollisionCallback) -> None
        """Add a collision handler."""
        self.collision_callbacks[(group1, group2)] = callback

    def dispatch_tick(self, elapsed_msec=None):
        # type: (int) -> None
        """Deal with time passing."""
        # calculate elapsed time since last tick
        curr_msec = Game.get_msec()
        if elapsed_msec is None:
            elapsed_msec = curr_msec - self.prev_msec
        # update all physics objects
        for obj in self.scene.objects:
            obj.update(elapsed_msec)
        # deal with collisions
        # FIXME use movement to optimize collision detection
        for obj1, obj2, group_pair in self.scene.collisions:
            self.collision_callbacks[group_pair](obj1, obj2)
        # draw all objects
        for game_object in self.scene.get_in_view(self.camera):
            self.camera.draw_sprite(game_object.get_sprite())
            #self.camera.draw_geometry(game_object.transformed_collision_geometry)
        # update timer
        self.prev_msec = curr_msec

    def prestart(self):
        # type: () -> None
        """Prepare the game to start.

        This function does all non-UI things needed to start the game; iti s in
        a separate function to facilitate testing.
        """
        self.prev_msec = Game.get_msec()
        self.scene.set_collision_group_pairs(self.collision_callbacks.keys())

    def start(self):
        # type: () -> None
        """Start the game."""
        for input_event, callback in self.keybinds.items():
            self.canvas.bind(input_event, callback)
        self.prestart()
        self.canvas.start(self.dispatch_tick, 40)

    @staticmethod
    def get_msec():
        # type: () -> int
        """Return a millisecond-level time."""
        return get_nsec_msec() // 1000
