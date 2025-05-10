"""A animabotics of code that may eventually resemble a game engine."""

from .algorithms import bentley_ottmann, triangulate_polygon
from .animation import AnimationController, Clip, Sprite, Shape
from .basic_window import BasicWindow
from .camera import Camera
from .canvas import Input, EventCallback, Canvas
from .color import Color
from .data_structures import SortedDict, SortedSet, PriorityQueue
from .game import Game
from .game_object import GameObject, PhysicsObject
from .matrix import Matrix, identity
from .metaprogramming import CachedMetaclass
from .polygon import ConvexPolygon, Polygon
from .scene import HierarchicalHashGrid
from .simplex import Geometry, Point2D, Vector2D, Segment, Triangle
from .transform import Transform
from .transformable import Transformable


__all__ = [
    'bentley_ottmann', 'triangulate_polygon',
    'AnimationController', 'Clip', 'Sprite', 'Shape',
    'BasicWindow',
    'Camera',
    'Canvas', 'Input', 'EventCallback', 'Canvas',
    'Color',
    'SortedDict', 'SortedSet', 'PriorityQueue',
    'Game',
    'GameObject', 'PhysicsObject',
    'Matrix', 'identity',
    'CachedMetaclass',
    'Polygon',
    'HierarchicalHashGrid',
    'Geometry', 'Point2D', 'Vector2D', 'Segment', 'Triangle',
    'Transform',
    'Transformable',
]
