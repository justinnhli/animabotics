"""A basic window for basic drawing."""

from math import sin, cos, pi as PI

from .animation import AnimationController, Sprite, Shape
from .canvas import Input
from .color import Color
from .game import Game
from .game_object import GameObject
from .simplex import Geometry, Point2D, Vector2D


class DummyGameObject(GameObject):
    """A dummy game object to hold a static geometry."""

    def __init__(self, geometry, fill_color=None, line_color=None):
        # type: (Geometry, Color, Color) -> None
        """Initialize the DummyGameObject."""
        super().__init__()
        self.collision_geometry = geometry
        self.animation = AnimationController.create_static_animation(Sprite([Shape(
            self.collision_geometry,
            fill_color,
            line_color,
        )]))
        # TODO solve the smallest-circle problem instead
        self.collision_radius = max(
            point.distance(self.position)
            for point in geometry.points
        )


class BasicWindow(Game):
    """A basic window for drawing static geometries."""

    def __init__(self, width, height):
        # type: (int, int) -> None
        """Initialize the BasicWindow."""
        super().__init__(width, height)
        for char in ['w', 's', 'a', 'd', 'e', 'q', ' ', 'r', 'f']:
            self.bind(Input(event_type='KeyPress', key_button=char), self.key_callback)

    def add_geometry(self, geometry, fill_color=None, line_color=None, z_level=0):
        # type: (Geometry, Color, Color) -> None
        """Add a geometry to be drawn."""
        obj = DummyGameObject(
            geometry,
            fill_color=fill_color,
            line_color=line_color,
        )
        obj.z_level = z_level
        self.add_object(obj)

    def key_callback(self, input_event, _):
        # type: (Input, Point2D) -> None
        """Deal with key presses."""
        translation = 25 / self.camera.zoom
        if input_event.key_button == 'w':
            self.camera.move_by(translation * Vector2D(sin(-self.camera.radians), cos(-self.camera.radians)))
        elif input_event.key_button == 's':
            self.camera.move_by(-translation * Vector2D(sin(-self.camera.radians), cos(-self.camera.radians)))
        elif input_event.key_button == 'a':
            self.camera.move_by(-translation * Vector2D(cos(self.camera.radians), sin(self.camera.radians)))
        elif input_event.key_button == 'd':
            self.camera.move_by(translation * Vector2D(cos(self.camera.radians), sin(self.camera.radians)))
        elif input_event.key_button == 'q':
            self.camera.rotate_by(PI / 8)
        elif input_event.key_button == 'e':
            self.camera.rotate_by(-PI / 8)
        elif input_event.key_button == ' ':
            self.camera.move_to(Point2D(0, 0))
            self.camera.rotate_to(0)
            self.camera.zoom_level = 0
        elif input_event.key_button == 'r':
            self.camera.zoom_level += 1
        elif input_event.key_button == 'f':
            self.camera.zoom_level -= 1
