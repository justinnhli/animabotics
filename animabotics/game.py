"""The abstract Game class."""

from enum import Enum
from collections import defaultdict
from typing import Any, Callable

from .camera import Camera
from .canvas import Input, EventCallback, Canvas
from .game_object import GameObject
from .scene import HierarchicalHashGrid
from .timing import get_msec
from .transformable import Collidable


CollisionCallback = Callable[[Collidable, Collidable], None]


class HookTrigger(Enum):
    """Enum for when callbacks are triggered."""
    PRE_UPDATE = 'PRE_UPDATE'
    POST_UPDATE = 'POST_UPDATE'


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
        self.objects = [] # type: list[GameObject]
        self.scene = HierarchicalHashGrid()
        self.collision_callbacks = {} # type: dict[tuple[str, str], CollisionCallback]
        self.bouncing_collision_group_pairs = set() # type: set[tuple[str, str]]
        # settings
        self.keybinds = {} # type: dict[Input, EventCallback]
        self.hooks = defaultdict(list) # type: dict[HookTrigger, list[Callable[[int, int], Any]]]
        # state
        self.prev_msec = None # type: int
        self.prev_collisions = set() # type: set[tuple[GameObject, GameObject, tuple[str, str]]]
        self.in_camera_objects = defaultdict(list) # type: dict[int, GameObject]
        # initialization
        self.camera.add_to_collision_group('_camera')
        self.on_collision(
            '_camera',
            None,
            (lambda _, game_object:
                self.in_camera_objects[game_object.z_level].append(game_object)
            ),
            debounce=False,
        )

    def add_object(self, game_object):
        # type: (GameObject) -> None
        """Add an object to the scene."""
        self.objects.append(game_object)

    def bind(self, input_event, callback):
        # type: (Input, EventCallback) -> None
        """Add a keybind."""
        self.keybinds[input_event] = callback

    def on_collision(self, group1, group2, callback, debounce=True):
        # type: (str, str, CollisionCallback, bool) -> None
        """Add a collision handler."""
        self.collision_callbacks[(group1, group2)] = callback
        if not debounce:
            self.bouncing_collision_group_pairs.add((group1, group2))

    def register_hook(self, hook_trigger, callback):
        # type: (HookTrigger, Callable[[int, int], Any]) -> None
        """Register a callback function."""
        assert isinstance(hook_trigger, HookTrigger)
        self.hooks[hook_trigger].append(callback)

    def run_for_msec(self, duration, update_every=40):
        # type: (int) -> None
        """Run for the specified time, updating at a fixed interval."""
        while duration > update_every:
            self.dispatch_tick(update_every)
            duration -= update_every
        self.dispatch_tick(duration)

    def dispatch_tick(self, elapsed_msec=None):
        # type: (int) -> None
        """Deal with time passing."""
        # calculate elapsed time since last tick
        curr_msec = get_msec()
        if elapsed_msec is None:
            elapsed_msec = curr_msec - self.prev_msec
        elapsed_msec_squared = elapsed_msec * elapsed_msec
        # call all pre-update hooks
        for callback in self.hooks[HookTrigger.PRE_UPDATE]:
            callback(curr_msec, elapsed_msec)
        # update all objects
        for obj in self.objects:
            obj.update(elapsed_msec, elapsed_msec_squared)
            self.scene.add(obj)
        self.scene.add(self.camera)
        # collect collisions
        new_collisions = set()
        call_back = set()
        for key in self.scene.collisions:
            obj1, obj2, group_pair = key
            new_collisions.add(key)
            trigger_callback = (
                key not in self.prev_collisions
                or group_pair in self.bouncing_collision_group_pairs
            )
            if trigger_callback:
                call_back.add(key)
        self.scene.clear()
        self.prev_collisions = new_collisions
        # trigger collision callbacks
        for obj1, obj2, group_pair in call_back:
            self.collision_callbacks[group_pair](obj1, obj2)
        # draw all objects
        for _, game_objects in sorted(self.in_camera_objects.items()):
            for game_object in game_objects:
                self.draw_recursive(game_object)
        self.in_camera_objects.clear()
        # call all post-update hooks
        for callback in self.hooks[HookTrigger.POST_UPDATE]:
            callback(curr_msec, elapsed_msec)
        # update timer
        self.prev_msec = curr_msec

    def draw_recursive(self, game_object):
        # type: (GameObject) -> None
        """Recursively draw a GameObject and its children."""
        self.camera.draw_sprite(game_object.sprite)
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
