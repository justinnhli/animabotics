"""GameObject and its hierarchy."""

from functools import cached_property
from typing import Iterator, Sequence

from .animation import Animation, Sprite, Shape
from .simplex import Geometry, Point2D, Vector2D
from .transformable import Transformable


class GameObject(Transformable):
    """A basic game object."""

    def __init__(
        self,
        collision_groups=None,
        position=None, rotation=0,
    ): # pylint: disable = unused-argument
        # type: (Sequence[str], Point2D, float) -> None
        """Initialize the GameObject."""
        super().__init__(position, rotation)
        self.animation = None # type: Animation
        self.collision_geometry = None # type: Geometry
        self.radius = 0 # type: float
        self._axis_projection_cache = {} # type: dict[tuple[Geometry, Vector2D], tuple[float, float]]
        self._collision_groups = frozenset() # type: frozenset[str]
        self._transformed_geometry_cache = {} # type: dict[PointsMatrix, PointsMatrix]
        self._transformed_sprite_cache = {} # type: dict[str, Sprite]
        if collision_groups:
            for group in collision_groups:
                self.add_to_collision_group(group)

    def __hash__(self):
        # type: () -> int
        return id(self)

    def __repr__(self):
        # type: () -> str
        return f'{type(self).__name__}({self.position})'

    @cached_property
    def transformed_collision_geometry(self):
        # type: () -> Geometry
        """The transformed Geometry."""
        return self.transform @ self.collision_geometry

    @cached_property
    def segment_normals(self):
        # type: () -> set[Vector2D]
        """Return the set of normal vectors to the perimeter."""
        result = set() # type: set[Vector2D]
        for segment in self.transformed_collision_geometry.segments:
            normal = segment.normal
            if normal.x < 0:
                normal = -normal
            result.add(normal)
        return result

    @property
    def collision_groups(self):
        # type: () -> frozenset[str]
        """Get the collision groups of the object."""
        return self._collision_groups

    def _transform_geometry(self, geometry):
        if geometry not in self._transformed_geometry_cache:
            self._transformed_geometry_cache[geometry] = self.transform @ geometry
        return self._transformed_geometry_cache[geometry]

    def get_sprite(self):
        # type: () -> Sprite
        """Get the current animation sprite."""
        return self.transform @ self.animation.get_sprite()

    def axis_projections(self, vector):
        # type: (Vector2D) -> Iterator[tuple[Geometry, float, float]]
        """Yield the min and max values of the points projected onto the vector."""
        cache = {} # type: dict[Point2D, float]
        denominator = (vector.x * vector.x + vector.y * vector.y) ** (1/2)
        for partition in self.transformed_collision_geometry.convex_partitions:
            key = (partition, vector)
            if key in self._axis_projection_cache:
                projected_min, projected_max = self._axis_projection_cache[key]
            else:
                projected = [] # type: list[float]
                for point in partition.points:
                    if point not in cache:
                        cache[point] = (vector.x * point.x + vector.y * point.y) / denominator
                    projected.append(cache[point])
                projected_min = min(projected)
                projected_max = max(projected)
            yield partition, projected_min, projected_max

    def cache_axis_projections(self):
        # type: () -> None
        """Cache the projections onto segment normals."""
        if self._axis_projection_cache:
            return
        for vector in self.segment_normals:
            for partition, projected_min, projected_max in self.axis_projections(vector):
                self._axis_projection_cache[(partition, vector)] = (projected_min, projected_max)

    def _clear_cache(self, rotated=False):
        # type: (bool) -> None
        """Clear the cached_property cache."""
        super()._clear_cache(rotated=rotated)
        # need to provide a default to avoid KeyError
        self.__dict__.pop('transformed_geometry', None)
        self.__dict__.pop('transformed_collision_geometry', None)
        self.__dict__.pop('segment_normals', None)
        self._transformed_geometry_cache.clear()
        if rotated:
            self._axis_projection_cache.clear()

    def update(self, elapsed_msec):
        # type: (int) -> None
        """Update the object."""
        if self.animation is not None:
            self.animation.advance_state(elapsed_msec)
        pass # pylint: disable = unnecessary-pass

    def squared_distance(self, other):
        # type: (GameObject) -> float
        """Calculate the squared distance to another object."""
        return self.position.squared_distance(other.position)

    def add_to_collision_group(self, group):
        # type: (str) -> None
        """Add the object to a collision group."""
        self._collision_groups |= set([group])

    def remove_from_collision_group(self, group):
        # type: (str) -> None
        """Remove the object from a collision group."""
        self._collision_groups -= set([group])

    def is_colliding(self, other):
        # type: (GameObject) -> bool
        """Determine if two objects are colliding.

        This uses the hyperplane separation/separating axis theorem, which
        states that if two convex objects are disjoint, there must be a line
        onto which the objects' projections are disjoint. Since the theorem
        only applies to convex objects, this implementation compares all pairs
        of triangles between the two polygons; if all pairs of triangles are
        separable, the polygons must also be disjoint.

        Additionally, the vector between the two centroids is tried first as a
        potential shortcut.
        """
        # trigger caching of axis projections
        self.cache_axis_projections()
        other.cache_axis_projections()
        # define convenience variables
        geometry1 = self.transformed_collision_geometry
        geometry2 = other.transformed_collision_geometry
        # try the vector between centroids first
        vector = (geometry1.centroid - geometry2.centroid).normalized
        if self.separated_on_axis(other, vector):
            return False
        # revert to the standard approach of trying all segment normals
        checked = set() # type: set[Vector2D]
        for obj in (self, other):
            for normal in obj.segment_normals:
                if normal in checked:
                    continue
                checked.add(normal)
                if self.separated_on_axis(other, normal):
                    return False
        return True

    def separated_on_axis(self, other, vector):
        # type: (GameObject, Vector2D) -> bool
        """Check if an axis separates two points matrices."""
        projections1 = self.axis_projections(vector)
        projections2 = other.axis_projections(vector)
        # this is essentially itertools.product(projections1, projections2),
        # but modified to not consume the entire generator unnecessarily
        _, min1, max1 = next(projections1)
        cache = []
        for partition2, min2, max2 in projections2:
            if min1 <= max2 and min2 <= max1:
                return False
            cache.append((partition2, min2, max2))
        for _, min1, max1 in projections1:
            for _, min2, max2 in cache:
                if min1 <= max2 and min2 <= max1:
                    return False
        return True


class PhysicsObject(GameObject):
    """A game object with kinematics."""

    def __init__(self):
        # type: () -> None
        """Initialize the PhysicsObject."""
        super().__init__()
        self.mass = 0
        self.velocity = Vector2D()
        self.angular_velocity = 0
        self.acceleration = Vector2D()
        self.angular_acceleration = 0

    def update(self, elapsed_msec):
        # type: (int) -> None
        """Update the velocity and the position."""
        super().update(elapsed_msec)
        self.velocity += self.acceleration * elapsed_msec / 1000
        self.angular_velocity += self.angular_acceleration * elapsed_msec / 1000
        if self.velocity:
            self.move_by(self.velocity * elapsed_msec / 1000)
        if self.angular_velocity:
            self.rotate_by(self.angular_velocity * elapsed_msec / 1000)
