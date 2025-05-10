"""A animabotics of code that may eventually resemble a game engine."""

from .algorithms import bentley_ottmann, triangulate_polygon
from .animation import AnimationController, Clip, Sprite, Shape
from .basic_window import BasicWindow
from .caching import CachedMetaclass, LRUCache, method_cache
from .camera import Camera
from .canvas import Input, EventCallback, Canvas
from .color import Color
from .components.component import Component, NeedsUpdates
from .components.drawable import Drawable, Unanimated, Animated
from .components.positionable import Positionable, HasPhysicsGeometry, Newtonian, Collidable
from .data_structures import HashGrid, SortedDict, SortedSet, PriorityQueue
from .game import Game, HookTrigger
from .matrix import Matrix, identity
from .polygon import ConvexPolygon, Polygon
from .scene import HierarchicalHashGrid
from .simplex import Geometry, Point2D, Vector2D, Segment, Triangle
from .timing import get_msec, InterruptibleAlgorithm
from .transform import Transform


__all__ = [
    'bentley_ottmann', 'triangulate_polygon',
    'AnimationController', 'Clip', 'Sprite', 'Shape',
    'BasicWindow',
    'CachedMetaclass', 'LRUCache', 'method_cache',
    'Camera',
    'Input', 'EventCallback', 'Canvas',
    'Color',
    'Component', 'NeedsUpdates',
    'Drawable', 'Unanimated', 'Animated',
    'Positionable', 'HasPhysicsGeometry', 'Newtonian', 'Collidable',
    'HashGrid', 'SortedDict', 'SortedSet', 'PriorityQueue',
    'Game', 'HookTrigger',
    'Matrix', 'identity',
    'ConvexPolygon', 'Polygon',
    'HierarchicalHashGrid',
    'Geometry', 'Point2D', 'Vector2D', 'Segment', 'Triangle',
    'get_msec', 'InterruptibleAlgorithm',
    'Transform',
]
