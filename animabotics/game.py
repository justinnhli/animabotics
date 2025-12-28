"""The abstract Game class."""

from typing import Callable

from .camera import Camera
from .canvas import Input, EventCallback, Canvas
from .game_object import GameObject
from .scene import HierarchicalHashGrid
from .timing import get_msec


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
        self.prev_collisions = set() # type: set[tuple[GameObject, GameObject]]

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
        curr_msec = get_msec()
        if elapsed_msec is None:
            elapsed_msec = curr_msec - self.prev_msec
        elapsed_msec_squared = elapsed_msec * elapsed_msec
        # update all objects
        for obj in self.scene.objects:
            obj.update(elapsed_msec, elapsed_msec_squared)
        # deal with collisions, with de-bouncing
        # FIXME use movement to optimize collision detection
        new_collisions = set()
        for obj1, obj2, group_pair in self.scene.collisions:
            key = (obj1, obj2)
            new_collisions.add(key)
            if key not in self.prev_collisions:
                self.collision_callbacks[group_pair](obj1, obj2)
        self.prev_collisions = new_collisions
        # draw all objects
        for game_object in self.scene.get_in_view(self.camera):
            self.draw_recursive(game_object)
        # update timer
        self.prev_msec = curr_msec

    def draw_recursive(self, game_object):
        # type: (GameObject) -> None
        """Recursively draw a GameObject and its children."""
        self.camera.draw_sprite(game_object.get_sprite())
        if hasattr(game_object, 'children'):
            for child in game_object.children:
                self.draw_recursive(child)

    def prestart(self):
        # type: () -> None
        """Prepare the game to start.

        This function does all non-UI things needed to start the game; it is in
        a separate function to facilitate testing.
        """
        self.prev_msec = get_msec()
        self.scene.set_collision_group_pairs(self.collision_callbacks.keys())

    def start(self):
        # type: () -> None
        """Start the game."""
        for input_event, callback in self.keybinds.items():
            self.canvas.bind(input_event, callback)
        self.prestart()
        self.canvas.start(self.dispatch_tick, 40)
