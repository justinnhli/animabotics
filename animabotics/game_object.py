"""GameObject and its hierarchy."""

from functools import cached_property
from typing import Sequence

from .animation import Animation, Sprite
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
        self.collision_radius = 0.0
        self._projection_cache = {} # type: dict[tuple[Geometry, Vector2D], tuple[float, float]]
        self._collision_groups = frozenset() # type: frozenset[str]
        if collision_groups:
            for group in collision_groups:
                self.add_to_collision_group(group)
        self.children = [] # type: list[GameObject]

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
    def partition_segment_normals(self):
        # type: () -> dict[Geometry, set[Vector2D]]
        """Calculate the segment normals of all partitions."""
        result = {}
        for partition in self.transformed_collision_geometry.convex_partitions:
            normals = set()
            for segment in partition.segments:
                normal = segment.normal
                if normal.x < 0:
                    normal = -normal
                normals.add(normal)
            result[partition] = normals
        return result

    @property
    def collision_groups(self):
        # type: () -> frozenset[str]
        """Get the collision groups of the object."""
        return self._collision_groups

    def get_sprite(self):
        # type: () -> Sprite
        """Get the current animation sprite."""
        return self.transform @ self.animation.get_sprite()

    def project_to_axis(self, geometry, vector):
        # type: (Geometry, Vector2D) -> tuple[float, float]
        """Project the geometry onto a vector (and cache it)."""
        key = (geometry, vector)
        if key not in self._projection_cache:
            self._projection_cache[key] = geometry.get_projected_range(vector)
        return self._projection_cache[key]

    def _clear_cache(self, rotated=False):
        # type: (bool) -> None
        """Clear the cached_property cache."""
        super()._clear_cache(rotated=rotated)
        # need to provide a default to avoid KeyError
        self.__dict__.pop('transformed_collision_geometry', None)
        self.__dict__.pop('partition_segment_normals', None)
        if rotated:
            self._projection_cache.clear()

    def update(self, elapsed_msec, _):
        # type: (int, int) -> None
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
        # try the vector between centroids first, unless the centroids are the same
        # may not collide even if centroids are the same (eg. a circle and a ring)
        vector = (
            self.transformed_collision_geometry.centroid
            - other.transformed_collision_geometry.centroid
        )
        if vector:
            separable = not self.is_overlapping_on_axis(
                self.transformed_collision_geometry,
                other.transformed_collision_geometry,
                vector.normalized,
            )
            if separable:
                return False
        # fall back to the standard approach of trying all segment normals of partitions
        for partition1, normals1 in self.partition_segment_normals.items():
            for partition2, normals2 in other.partition_segment_normals.items():
                separable = not all(
                    self.is_overlapping_on_axis(partition1, partition2, normal)
                    for normal in set.union(normals1, normals2)
                )
                if not separable:
                    return True
        return False

    def is_overlapping_on_axis(self, geometry1, geometry2, vector):
        # type: (Geometry, Geometry, Vector2D) -> bool
        """Check if an axis separates two points matrices."""
        min1, max1 = self.project_to_axis(geometry1, vector)
        min2, max2 = self.project_to_axis(geometry2, vector)
        return min1 <= max2 and min2 <= max1


class PhysicsObject(GameObject):
    """A game object with kinematics."""

    def __init__(self):
        # type: () -> None
        """Initialize the PhysicsObject."""
        super().__init__()
        self.mass = 0
        self.velocity = Vector2D()
        self.angular_velocity = 0.0
        self.acceleration = Vector2D()
        self.angular_acceleration = 0.0

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the velocity and the position."""
        super().update(elapsed_msec, elapsed_msec_squared)
        prev_velocity = self.velocity
        self.velocity += self.acceleration * elapsed_msec
        self.angular_velocity += self.angular_acceleration * elapsed_msec
        if self.velocity:
            self.move_by(prev_velocity * elapsed_msec + 0.5 * self.acceleration * elapsed_msec_squared)
        if self.angular_velocity:
            self.rotate_by(self.angular_velocity * elapsed_msec)
