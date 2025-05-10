#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for time slicing."""

# pylint: disable = wrong-import-position

import sys
from collections import defaultdict
from math import sqrt
from pathlib import Path
from random import Random
from typing import Iterator

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import Game, HookTrigger
from animabotics import InterruptibleAlgorithm
from animabotics import HashGrid
from animabotics import Shape
from animabotics import Point2D, Segment, Triangle, Polygon
from animabotics import Unanimated, Color
from animabotics import Collidable
from animabotics import get_msec


class ArtPoint(Unanimated):
    """A point object in the artwork."""

    SHAPE = Shape(
        Polygon.ellipse(2, 2),
        fill_color=Color.from_hex('#A0A0A0FF'),
    )

    def __init__(self, x, y):
        # type: (int, int) -> None
        super().__init__(
            position=Point2D(x, y),
            sprite_or_shapes=ArtPoint.SHAPE,
            z_level=3,
        )


class ArtSegment(Unanimated, Collidable):
    """A segment object in the artwork."""

    def __init__(self, point1, point2):
        # type: (Point2D, Point2D) -> None
        self.point1 = point1
        self.point2 = point2
        self.segment = Segment(point1, point2)
        centroid = self.segment.centroid.to_vector()
        segment = Segment(point1 - centroid, point2 - centroid)
        super().__init__(
            position=centroid,
            sprite_or_shapes=Shape(
                segment,
                line_color=Color.from_hex('#D0D0D0FF'),
            ),
            physics_geometry=segment,
            z_level=2,
        )


class ArtTriangle(Unanimated):
    """A triangle object in the artwork."""

    def __init__(self, point1, point2, point3, color):
        # type: (Point2D, Point2D, Point2D, Color) -> None
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3
        centroid = Triangle(point1, point2, point3).centroid.to_vector()
        triangle = Triangle(
            point1 - centroid,
            point2 - centroid,
            point3 - centroid,
        )
        super().__init__(
            position=centroid,
            sprite_or_shapes=Shape(
                triangle,
                line_color=Color.from_hex('#E0E0E0FF'),
                fill_color=color,
            ),
            z_level=1,
        )


class TriangleArt(InterruptibleAlgorithm):
    """The algorithm for create works of triangle art."""

    PIXELS_PER_MILLION = 750
    MAX_ATTEMPTS = 10
    WAIT_MSEC = 10000 # ten seconds

    def __init__(self, width, height, rng=None):
        # type: (int, int, Random) -> None
        super().__init__()
        # constants
        self.width = width
        self.height = height
        self.num_points = round(TriangleArt.PIXELS_PER_MILLION * (self.width * self.height) // 1000000)
        self.half_width = self.width // 2
        self.half_height = self.height // 2
        self.max_segment_length = min(self.width, self.height) // 5
        self.min_segment_length = self.max_segment_length // 3
        if rng is None:
            self.rng = Random()
        else:
            self.rng = rng
        # variables
        self._completed = False
        self.palette = [] # type: list[Color]
        self.points = HashGrid(int(self.min_segment_length / sqrt(2))) # type: HashGrid[ArtPoint]
        self.sorted_points = [] # type: list[ArtPoint]
        self.segments = [] # type: list[tuple[float, ArtSegment]]
        self.sorted_segments = [] # type: list[ArtSegment]
        self.triangles = defaultdict(list) # type: dict[ArtSegment, list[ArtTriangle]]

    @property
    def completed(self):
        # type: () -> bool
        return self._completed

    def restart(self):
        # type: () -> None
        self._completed = False
        self.palette = []
        self.points.clear()
        self.sorted_points.clear()
        self.segments.clear()
        self.sorted_segments.clear()
        self.triangles.clear()

    def hurry_up_and_wait(self):
        # type: () -> Iterator[None]
        self.restart()
        self.create_palette()
        yield
        yield from self.create_border_points()
        yield from self.create_inside_points()
        self.sorted_points = list(self.points.objects)
        self.rng.shuffle(self.sorted_points)
        yield
        yield from self.create_segments()
        self._completed = True

    def create_palette(self, count=100):
        # type: (int) -> None
        """Create the palette for this work."""
        hue = self.rng.random()
        hue_range = self.rng.choice([0, 0.03, 0.1])
        self.palette = [
            Color(
                (hue + self.rng.uniform(0, hue_range) - (hue_range / 2)) % 1,
                self.rng.uniform(0.2, 0.8),
                self.rng.uniform(0.2, 0.8),
            )
            for _ in range(count)
        ]

    def _add_point(self, new_point):
        # type: (ArtPoint) -> None
        for other_point in self.points.nearest_neighbors(new_point.position, k=10000):
            distance = (other_point.position - new_point.position).magnitude
            assert distance > 0
            if distance < 1.5 * self.max_segment_length:
                self.segments.append((distance, ArtSegment(other_point.position, new_point.position)))
            else:
                break
        self.points.add(new_point)

    def create_border_points(self):
        # type: () -> Iterator[None]
        """Add points on the border of the work."""
        # corners
        self._add_point(ArtPoint(-self.half_width, -self.half_height))
        self._add_point(ArtPoint(-self.half_width, self.half_height))
        self._add_point(ArtPoint(self.half_width, -self.half_height))
        self._add_point(ArtPoint(self.half_width, self.half_height))
        yield
        # bottom border
        for offset in self._bridson_poisson_disk_1d(self.width)[1:-1]:
            self._add_point(ArtPoint(offset - self.half_width, -self.half_height))
        yield
        # top border
        for offset in self._bridson_poisson_disk_1d(self.width)[1:-1]:
            self._add_point(ArtPoint(offset - self.half_width, self.half_height))
        yield
        # left border
        for offset in self._bridson_poisson_disk_1d(self.height)[1:-1]:
            self._add_point(ArtPoint(-self.half_width, offset - self.half_height))
        yield
        # right border
        for offset in self._bridson_poisson_disk_1d(self.height)[1:-1]:
            self._add_point(ArtPoint(self.half_width, offset - self.half_height))
        yield

    def _bridson_poisson_disk_1d(self, length, min_dist=None, max_dist=None, max_tries=10):
        # type: (int, int, int, int) -> list[int]
        """Create points using an adapted version of Bridson's Poisson disk sampling algorithm."""
        if min_dist is None:
            min_dist = self.min_segment_length
        if max_dist is None:
            max_dist = self.max_segment_length
        points = [0]
        while True:
            for _ in range(max_tries):
                new_point = self.rng.randrange(min_dist, max_dist) + points[-1]
                if length - new_point > min_dist:
                    points.append(new_point)
                    break
            if min_dist <= length - points[-1] <= max_dist:
                return points + [length]

    def create_inside_points(self):
        # type: () -> Iterator[None]
        """Add points on the interior of the work."""
        while len(self.points) < self.num_points:
            for _ in range(TriangleArt.MAX_ATTEMPTS):
                new_point = ArtPoint(
                    self.rng.randrange(self.width) - self.half_width,
                    self.rng.randrange(self.height) - self.half_height,
                )
                nearest_neighbor_dist = (
                    list(self.points.nearest_neighbors(new_point.position, k=1))[0].position
                    - new_point.position
                ).magnitude
                if nearest_neighbor_dist >= self.min_segment_length:
                    self._add_point(new_point)
                    break
            yield

    def create_segments(self):
        # type: () -> Iterator[None]
        """Connect points without leading to intersecting segments."""
        segment_collider = HashGrid(int(self.max_segment_length)) # type: HashGrid[ArtSegment]
        connections = defaultdict(set) # type: dict[Point2D, set[Point2D]]
        for _, segment in sorted(self.segments, key=(lambda pair: pair[0])):
            collisions = False
            for other_segment in segment_collider.nearest_neighbors(segment.position):
                distance = (other_segment.position - segment.position).magnitude
                if distance > (segment.segment.length + other_segment.segment.length) / 2:
                    continue
                if segment.segment.intersect(other_segment.segment, include_end=False) is not None:
                    collisions = True
                    break
            if not collisions:
                self.sorted_segments.append(segment)
                segment_collider.add(segment)
                point1 = segment.point1
                point2 = segment.point2
                for point3 in connections[point1].intersection(connections[point2]):
                    orientation = Segment.orientation(
                        point1,
                        point2,
                        point3,
                    )
                    if orientation == -1:
                        points = (point1, point2, point3)
                    else:
                        points = (point3, point2, point1)
                    self.triangles[segment].append(ArtTriangle(*points, self.rng.choice(self.palette)))
                connections[point1].add(point2)
                connections[point2].add(point1)
            yield


class Background(Unanimated):
    """A dummy rectangle for the background."""

    def __init__(self, width, height):
        # type: (int, int) -> None
        super().__init__(
            position=Point2D(0, 0),
            sprite_or_shapes=Shape(
                Polygon.rectangle(width, height),
                fill_color=Color.from_hex('#E0E0E0FF'),
            ),
        )


class TimeSlicingDemo(Game):
    """A generative art time slicing demonstration."""

    def __init__(self, random_seed=None):
        # type: (int) -> None
        super().__init__(600, 400)
        # constants
        width = 600
        height = 400
        # variables
        self.rng = Random(random_seed)
        self.curr_work = TriangleArt(width, height, rng=self.rng)
        self.next_work = TriangleArt(width, height, rng=self.rng)
        self.turnover_msec = None # type: int
        self.points_index = 0
        self.segments_index = 0
        self.background = Background(width, height)
        # set up hooks
        self.register_hook(HookTrigger.PRE_UPDATE, self.create_entities)
        self.register_hook(HookTrigger.POST_UPDATE, self.generate_art)
        # generate the first work
        self.add_entity(self.background)
        self.curr_work.run()

    def create_entities(self, _1, _2, _3):
        # type: (int, int, int) -> None
        """Create entities from the objects in the art work."""
        if self.points_index < len(self.curr_work.sorted_points):
            # create points
            self.add_entity(self.curr_work.sorted_points[self.points_index])
            self.points_index += 1
        elif self.segments_index < len(self.curr_work.sorted_segments):
            # create segments and triangles
            segment = self.curr_work.sorted_segments[self.segments_index]
            self.add_entity(segment)
            for triangle in self.curr_work.triangles[segment]:
                self.add_entity(triangle)
            self.segments_index += 1
        elif self.turnover_msec is None:
            self.turnover_msec = get_msec() + TriangleArt.WAIT_MSEC

    def generate_art(self, tick_start_msec, _1, _2):
        # type: (int, int, int) -> None
        """Generate the next work of triangular art."""
        if not self.next_work.completed:
            # if the next work is not complete, resume work on it
            time = (tick_start_msec + 40 - get_msec()) - 10 # one frame plus 7 msec for safety
            self.next_work.run_for_msec(time)
        elif self.turnover_msec is not None and tick_start_msec >= self.turnover_msec:
            # if it's time to switch, reset the variables
            self.curr_work, self.next_work = self.next_work, self.curr_work
            self.clear_entities()
            self.add_entity(self.background)
            self.points_index = 0
            self.segments_index = 0
            self.turnover_msec = None
            self.next_work.restart()


def main(): # pragma: no cover
    # type: () -> None
    """Provide a CLI entry point."""
    TimeSlicingDemo().start()


if __name__ == '__main__':
    main()
