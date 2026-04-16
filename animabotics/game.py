"""The abstract Game class."""

from enum import Enum
from collections import defaultdict
from typing import Any, Callable

from .camera import Camera
from .canvas import Input, EventCallback, Canvas
from .components import Component, Collidable, Drawable, NeedsUpdates
from .scene import HierarchicalHashGrid


HookCallback = Callable[[int], Any]
CollisionCallback = Callable[[Collidable, Collidable], Any]


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
        # entities
        self.component_entities_map = defaultdict(set) # type: dict[type, set[Component]]
        self.scene = HierarchicalHashGrid()
        self.collision_callbacks = {} # type: dict[tuple[str, str], CollisionCallback]
        self.bouncing_collision_group_pairs = set() # type: set[tuple[str, str]]
        # settings
        self.keybinds = {} # type: dict[Input, EventCallback]
        self.hooks = defaultdict(list) # type: dict[HookTrigger, list[HookCallback]]
        # state
        self.prev_collisions = set() # type: set[tuple[Collidable, Collidable, tuple[str, str]]]

    def add_entity(self, entity):
        # type: (Component) -> None
        """Add an entity to the game."""
        for component_cls in entity.components:
            self.component_entities_map[component_cls].add(entity)

    @property
    def entities(self):
        return self.get_component_entities(Component)

    def get_component_entities(self, *components):
        # type: (*type[Component]) -> set[Component]
        """Get all entities with the given components."""
        return set.union(*(
            self.component_entities_map[component] for component in components
        ))

    def remove_entity(self, entity):
        """Remove an entity from the game."""
        for component_cls in entity.components:
            self.component_entities_map[component_cls].remove(entity)

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
        # type: (HookTrigger, HookCallback) -> None
        """Register a callback function."""
        assert isinstance(hook_trigger, HookTrigger)
        self.hooks[hook_trigger].append(callback)

    def run_for_msec(self, duration, update_every=40):
        # type: (int, int) -> None
        """Run for the specified time, updating at a fixed interval."""
        while duration > update_every:
            self.dispatch_tick(update_every)
            duration -= update_every
        self.dispatch_tick(duration)

    def dispatch_tick(self, elapsed_msec):
        # type: (int) -> None
        """Deal with time passing."""
        # calculate elapsed time since last tick
        elapsed_msec_squared = elapsed_msec * elapsed_msec
        # call all pre-update hooks
        for callback in self.hooks[HookTrigger.PRE_UPDATE]:
            callback(elapsed_msec)
        # update entities
        for entity in self.get_component_entities(NeedsUpdates):
            assert isinstance(entity, NeedsUpdates)
            entity.update(elapsed_msec, elapsed_msec_squared)
        # add all collidable entities to the scene
        for entity in self.get_component_entities(Collidable):
            assert isinstance(entity, Collidable)
            self.scene.add(entity)
        # collect collisions
        new_collisions = set()
        call_back = set()
        for key in self.scene.collisions:
            entity1, entity2, group_pair = key
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
        for entity1, entity2, group_pair in call_back:
            self.collision_callbacks[group_pair](entity1, entity2)
        # draw entities
        # FIXME need to separate drawing from collision
        # in its simplest form: do a separate hierarchical grid for Drawables
        # this is inefficient: collision is many-to-many, while culling is one to many
        for entity in self.get_component_entities(Drawable):
            assert isinstance(entity, Drawable)
            self.draw_recursive(entity)
        # call all post-update hooks
        for callback in self.hooks[HookTrigger.POST_UPDATE]:
            callback(elapsed_msec)

    def draw_recursive(self, entity):
        # type: (Drawable) -> None
        """Recursively draw an entity and its children."""
        self.camera.draw_sprite(entity.transformed_sprite())
        if hasattr(entity, 'children'):
            for child in entity.children:
                self.draw_recursive(child)

    def prestart(self):
        # type: () -> None
        """Prepare the game to start.

        This function does all non-UI things needed to start the game; it is in
        a separate function to facilitate testing.
        """
        self.scene.set_collision_group_pairs(self.collision_callbacks.keys())

    def start(self):
        # type: () -> None
        """Start the game."""
        for input_event, callback in self.keybinds.items():
            self.canvas.bind(input_event, callback)
        self.prestart()
        self.canvas.start(self.dispatch_tick, 40)
