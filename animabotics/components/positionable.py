"""An abstract class for something that is transformable."""

from functools import cached_property
from typing import Any, Iterator, Sequence

from .component import Component, NeedsUpdates
from ..simplex import Geometry, Point2D, Vector2D
from ..transform import Transform


class Positionable(Component):
    """A component for position and rotation."""

    def __init__(self, position=None, rotation=0, **kwargs):
        # type: (Point2D, float, **Any) -> None
        super().__init__(**kwargs)
        if position is None:
            self._position = Point2D()
        else:
            self._position = position
        self._rotation = rotation

    @property
    def position(self):
        # type: () -> Point2D
        """Return the position."""
        return self._position

    @property
    def rotation(self):
        # type: () -> float
        """Return the rotation in radians."""
        return self._rotation

    @cached_property
    def transform(self):
        # type: () -> Transform
        """The transform defined by the position of this object."""
        return Transform(self.position.x, self.position.y, self.rotation)

    def _clear_cache(self, rotated=False):
        # type: (bool) -> None
        """Clear the cached_property cache."""
        # pylint: disable = unused-argument
        # need to provide a default to avoid KeyError
        self.__dict__.pop('transform', None)

    def move_to(self, point):
        # type: (Point2D) -> None
        """Move the object to the point."""
        self._position = point
        self._clear_cache()

    def move_by(self, vector):
        # type: (Vector2D) -> None
        """Move the object by the vector."""
        self._position += vector
        self._clear_cache()

    def rotate_to(self, rotation):
        # type: (float) -> None
        """Rotate the object to the angle."""
        self._rotation = rotation
        self._clear_cache(rotated=True)

    def rotate_by(self, rotation):
        # type: (float) -> None
        """Rotate the object by the angle."""
        self._rotation += rotation
        self._clear_cache(rotated=True)

    def squared_distance(self, other):
        # type: (Positionable) -> float
        """Calculate the squared distance to another object."""
        return self.position.squared_distance(other.position)


class HasPhysicsGeometry(Component):

    def __init__(self, physics_geometry, **kwargs):
        # type: (Geometry, **Any) -> None
        super().__init__(**kwargs)
        self._physics_geometry = physics_geometry

    @property
    def physics_geometry(self):
        # type: () -> Geometry
        """Get the physics geometry."""
        return self._physics_geometry

    @physics_geometry.setter
    def physics_geometry(self, physics_geometry):
        # type: (Geometry) -> None
        """Set the physics geometry."""
        self._physics_geometry = physics_geometry
        self.__dict__.pop('physics_radius', None)

    @cached_property
    def physics_radius(self):
        # type: () -> float
        """Calculate the maximum radius of the physics geometry."""
        # TODO solve the smallest-circle problem instead
        max_distance = 0.0
        for point in self.physics_geometry.points:
            max_distance = max(max_distance, point.to_vector().magnitude)
        return max_distance


class Newtonian(Positionable, HasPhysicsGeometry, NeedsUpdates):
    """A component for objects following Newtonian mechanics."""

    def __init__(
            self,
            mass,
            velocity=None,
            angular_velocity=None,
            center_of_mass=None,
            **kwargs
        ):
        # type: (float, Vector2D, float, Point2D, **Any) -> None
        super().__init__(**kwargs)
        assert mass is not None
        self.mass = mass
        if velocity is None:
            self.velocity = Vector2D()
        else:
            self.velocity = velocity
        if angular_velocity is None:
            self.angular_velocity = 0.0
        else:
            self.angular_velocity = angular_velocity
        if center_of_mass is None:
            self.center_of_mass = Point2D()
        else:
            self.center_of_mass = center_of_mass
        self.forces = [] # type: list[tuple[Vector2D, Point2D]]

    @property
    def kinetic_energy(self):
        # type: () -> float
        """Calculate the kinetic energy."""
        return 0.5 * self.mass * self.velocity.magnitude ** 2

    def moment_of_inertia(self, center_of_rotation):
        # type: (Point2D) -> float
        """Calculate the moment of inertia for a given center of rotation as a point mass."""
        return self.mass * (self.center_of_mass - center_of_rotation).magnitude ** 2

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the velocity and the position."""
        net_force, net_torque = self.sum_forces(self.forces)
        # translate net force into global coordinates
        net_force = self.transform @ net_force
        self.forces.clear()
        acceleration = net_force / self.mass
        angular_acceleration = net_torque / self.mass
        if self.velocity or acceleration:
            self.move_by(
                self.velocity * elapsed_msec
                + 0.5 * acceleration * elapsed_msec_squared
            )
        if self.angular_velocity or angular_acceleration:
            self.rotate_by(
                self.angular_velocity * elapsed_msec
                + 0.5 * angular_acceleration * elapsed_msec_squared
            )
        self.velocity += acceleration * elapsed_msec
        self.angular_velocity += angular_acceleration * elapsed_msec

    def apply_force(self, vector, position=None):
        # type: (Vector2D, Point2D) -> None
        """Apply a local force."""
        if position is None:
            position = Point2D()
        self.forces.append((vector, position))

    def sum_forces(self, forces):
        # type: (list[tuple[Vector2D, Point2D]]) -> tuple[Vector2D, float]
        """Sum up forces to determine net force and net torque."""
        net_force = Vector2D()
        net_torque = 0.0
        for force, position in forces:
            net_force += force
            net_torque += position.matrix.cross(force.matrix).z
        return net_force, net_torque


class Collidable(Positionable, HasPhysicsGeometry):
    """A component for collidable objects."""

    def __init__(self, collision_geometry, collision_groups=None, **kwargs):
        # type: (Geometry, Sequence[str], **Any) -> None
        super().__init__(**kwargs)
        self._collision_geometry = collision_geometry
        if collision_groups:
            self._collision_groups = frozenset(collision_groups) # type: frozenset[str]
        else:
            self._collision_groups = frozenset()
        self._projection_cache = {} # type: dict[tuple[Geometry, Vector2D], tuple[float, float]]

    @property
    def collision_geometry(self):
        # type: () -> Geometry
        """Return the collision geometry."""
        return self._collision_geometry

    @cached_property
    def segment_normals(self):
        # type: () -> tuple[set[Vector2D], ...]
        """Calculate the segment normals of all partitions."""
        result = []
        for partition in self.transformed_collision_geometry.convex_partitions:
            normals = set()
            for segment in partition.segments:
                normal = segment.normal
                if normal.x < 0:
                    normal = -normal
                normals.add(normal)
            result.append(normals)
        return tuple(result)

    @property
    def partition_segment_normals(self):
        # type: () -> Iterator[tuple[Geometry, set[Vector2D]]]
        """Calculate the segment normals of all partitions."""
        yield from zip(
            self.transformed_collision_geometry.convex_partitions,
            self.segment_normals,
            strict=True,
        )

    @cached_property
    def transformed_collision_geometry(self):
        # type: () -> Geometry
        """The transformed Geometry."""
        return self.transform @ self.collision_geometry

    @property
    def collision_groups(self):
        # type: () -> frozenset[str]
        """Get the collision groups of the object."""
        return self._collision_groups

    def _clear_cache(self, rotated=False):
        # type: (bool) -> None
        """Clear the cached_property cache."""
        super()._clear_cache(rotated=rotated)
        # need to provide a default to avoid KeyError
        self.__dict__.pop('transformed_collision_geometry', None)
        self._projection_cache.clear()
        if rotated:
            self.__dict__.pop('segment_normals', None)

    def add_to_collision_group(self, group):
        # type: (str) -> None
        """Add the object to a collision group."""
        self._collision_groups |= set([group])

    def remove_from_collision_group(self, group):
        # type: (str) -> None
        """Remove the object from a collision group."""
        self._collision_groups -= set([group])

    def project_to_axis(self, geometry, vector, cache=False):
        # type: (Geometry, Vector2D, bool) -> tuple[float, float]
        """Project the geometry onto a vector (and cache it)."""
        key = (geometry, vector)
        if key in self._projection_cache:
            result = self._projection_cache[key]
        else:
            result = geometry.get_projected_range(vector)
            if cache:
                self._projection_cache[key] = result
        return result

    def is_colliding(self, other):
        # type: (Collidable) -> bool
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
            colliding = self.is_overlapping_on_axis(
                other,
                self.transformed_collision_geometry,
                other.transformed_collision_geometry,
                vector.normalized,
                cache=False,
            )
            if not colliding:
                return False
        # fall back to the standard approach of trying all segment normals of partitions
        for partition1, normals1 in self.partition_segment_normals:
            for partition2, normals2 in other.partition_segment_normals:
                colliding = (
                    all(
                        self.is_overlapping_on_axis(other, partition1, partition2, normal)
                        for normal in normals1
                    ) and all(
                        other.is_overlapping_on_axis(self, partition2, partition1, normal)
                        for normal in normals2
                    )
                )
                if colliding:
                    return True
        return False

    def is_overlapping_on_axis(self, other, geometry1, geometry2, vector, cache=True):
        # type: (Collidable, Geometry, Geometry, Vector2D, bool) -> bool
        """Check if an axis separates two points matrices."""
        min1, max1 = self.project_to_axis(geometry1, vector, cache=cache)
        min2, max2 = other.project_to_axis(geometry2, vector, cache=False)
        return min1 <= max2 and min2 <= max1
