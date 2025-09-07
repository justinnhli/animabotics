"""Utility algorithms."""

from collections import defaultdict, Counter, namedtuple
from collections.abc import Sequence
from enum import IntEnum, Enum
from math import inf as INF, pi as PI, copysign, nextafter
from typing import Any, Optional, Union

from .data_structures import SortedDict, PriorityQueue
from .simplex import Point2D, Segment


class _SegmentWrapper:
    """A wrapper class for ordering Segments in sweep line algorithms."""

    sweep_x = -INF

    def __init__(self, segment):
        # type: (Segment) -> None
        self.segment = segment
        self._x = None # type: Optional[float]
        self._y = None # type: Optional[float]

    def __eq__(self, other):
        # type: (Any) -> bool
        assert isinstance(other, type(self))
        return self.segment == other.segment

    def __lt__(self, other):
        # type: (Any) -> bool
        if isinstance(other, type(self)):
            return self.key < other.key
        elif isinstance(other, (int, float)):
            return self.y < other
        else:
            raise TypeError(f"'<' not supported between instances of 'Segment' and '{type(other)}'")

    def __gt__(self, other):
        # type: (Any) -> bool
        if isinstance(other, type(self)):
            return self.key > other.key
        elif isinstance(other, (int, float)):
            return self.y > other
        else:
            raise TypeError(f"'>' not supported between instances of 'Segment' and '{type(other)}'")

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'{type(self).__name__}@{self.sweep_x}({self.segment.point1}, {self.segment.point2})'

    @property
    def key(self):
        # type: () -> Any
        """Return the comparison key."""
        raise NotImplementedError()

    @property
    def y(self):
        # type: () -> float
        """Return the correct y value at sweep_x."""
        if self._x != self.sweep_x:
            self._update_y()
        return self._y

    @y.setter
    def y(self, value):
        # type: (float) -> None
        """Set the value of y forcefully."""
        self._x = self.sweep_x
        self._y = value

    def _update_y(self):
        # type: () -> None
        self._x = self.sweep_x
        if self.segment.point1.x == self.segment.point2.x:
            if self._y is None:
                self._y = self.segment.min_y
        else:
            self._y = self.segment.point_at(self._x).y


def bentley_ottmann(segments, include_end=False, ndigits=9): # pylint: disable = too-many-statements
    # type: (Sequence[Segment], bool, int) -> list[Point2D]
    """Implement the Bentley-Ottmann all intersects algorithm.

    The Bentley-Ottmann algorithm is a sweep line algorithm for finding all
    intersects of given segments. Using a vertical sweep line over the
    endpoints of the segments (in a priority queue), it additionally uses a
    balanced binary search tree to track the y-values of each segment. Only
    the intersects of adjacent segments are calculated and added to the
    priority queue. At every endpoint and intersect, the tree is updated,
    and the appropriate events added and  removed from the priority queue.
    This allows the algorithm to have O((n + k)log(n)) complexity, where n
    is the number of segments and k the number of intersects.

    The heart of the algorithm is updating the tree to determine segments
    are adjacent. This is complicated because every segment could have new
    y-values, but the complexity requires only log(n) of them be updated at
    every endpoint/intersect. The naive way of doing this - looping over all
    segments in the tree - would require O(n^2) time. This can be seen in
    the case of n parallel segments, as each new segment requires updating
    all previous segments. Instead, the trick is to recognize that the order
    of the segments cannot change during this update, as otherwise we would
    have had a "meet" event first. The correct way to do this is therefore
    to do update the keys ONLY OF SEGMENTS ON THE PATH DOWN FROM THE ROOT TO
    THE NEW LEAF. The tree would lose the binary search tree property, but
    that's okay, because:

    * since the order doesn't change, updating the key would never point to
      the incorrect child, even if the un-updated child ends up on the
      "wrong" side of its parent
    * the keys that are not updated are, by definition, irrelevant for the
      purpose of determining the intersects of the new segment, although the
      previous and next nodes may need to be updated as well
    * when those un-updated keys are needed, it will either be due to a new
      segment (dealt with above) or a crossing, at which point they can be
      swapped without affecting the order of anything else in the tree
    * when rotating on the way back up after insertion, some additional keys
      may need to be updated, but only O(log n) keys in the worst case, and
      again the order does not change

    In other words, because the relevant keys are updated when necessary,
    the tree can be considered "eventual consistent" (to borrow from
    database terminology). This relaxation of the binary search tree
    property allows for insertion, search, and removal to all remain
    O(log n), and the overall Bentley-Ottmann algorithm to remain
    O((n + k)log(n))

    This implementation assumes that segments do not overlap, but otherwise
    deals with intersections of endpoints, intersections of three of more
    segments, vertical segments, and other edge cases. This is supported by
    a two modifications to the basic algorithm:

    * intersects also record which segments generated them, and intersects
      of more than two segments are merged and dealt with simultaneously

    * orderings of segments and intersects use additional properties to
      accommodate kissing and vertical segments
    """

    class BOEvent(IntEnum):
        """Enum for different Bentley-Ottmann events."""

        START = 1
        MEET = 2
        END = 3

    class BOSegmentWrapper(_SegmentWrapper):
        """A wrapper class for ordering Segments."""

        @property
        def key(self):
            # type: () -> tuple[float, float, Segment]
            """Return the comparison key.

            When the y-value is the same, this key sorts segments by the
            vertical order on the left side.
            """
            return (self.y, -self.segment.slope, self.segment)

    Priority = tuple[float, BOEvent, Union[float, Segment]]

    # initialize the two main data structures
    priority_queue = PriorityQueue() # type: PriorityQueue[Priority, tuple[BOEvent, Union[Point2D, Segment]]]
    tree = SortedDict() # type: SortedDict[BOSegmentWrapper, Segment]
    for segment in segments:
        segment = min(segment, segment.twin)
        priority_queue.push(
            (BOEvent.START, segment),
            (segment.min_x, BOEvent.START, segment),
        )
        priority_queue.push(
            (BOEvent.END, segment),
            (segment.max_x, BOEvent.END, segment),
        )
    # initialize additional state-keeping structures
    segment_wrappers = {} # type: dict[Segment, BOSegmentWrapper]
    intersect_cache = {} # type: dict[tuple[Segment, Segment], Point2D]
    intersect_segment_counts = defaultdict(Counter) # type: dict[Point2D, Counter[Segment]]
    segment_intersect_map = defaultdict(dict) # type: dict[Segment, dict[Point2D, bool]]

    def get_intersect(segment1, segment2):
        # type: (Segment, Segment) -> Point2D
        # need to deal with all intersects, including ends, to keep tree in order
        if segment1 < segment2:
            intersect_key = (segment1, segment2)
        else:
            intersect_key = (segment2, segment1)
        if intersect_key not in intersect_cache:
            intersect = segment1.intersect(segment2, include_end=True)
            if intersect is not None:
                intersect = round(intersect, ndigits=ndigits)
                segment_intersect_map[segment1][intersect] = (
                    intersect not in (segment1.point1, segment1.point2)
                )
                segment_intersect_map[segment2][intersect] = (
                    intersect not in (segment2.point1, segment2.point2)
                )
            intersect_cache[intersect_key] = intersect
        return intersect_cache[intersect_key]

    def get_tree_neighbors(segment):
        # type: (Segment) -> list[Segment]
        cursor = tree.cursor(segment_wrappers[segment])
        neighbors = []
        if cursor.has_prev:
            neighbors.append(cursor.prev().value)
        if cursor.has_next:
            neighbors.append(cursor.next().value)
        return neighbors

    def schedule_intersect(segment1, segment2):
        # type: (Segment, Segment) -> None
        intersect = get_intersect(segment1, segment2)
        if intersect is None:
            return
        # check that intersection is after sweep line
        if intersect.x < BOSegmentWrapper.sweep_x:
            return
        if intersect_segment_counts[intersect].total() == 0:
            priority_queue.push(
                (BOEvent.MEET, intersect),
                (intersect.x, BOEvent.MEET, intersect.y),
            )
        intersect_segment_counts[intersect][segment1] += 1
        intersect_segment_counts[intersect][segment2] += 1

    def unschedule_intersect(segment1, segment2):
        # type: (Segment, Segment) -> None
        intersect = get_intersect(segment1, segment2)
        if intersect is None:
            return
        if intersect.x <= BOSegmentWrapper.sweep_x:
            return
        intersect_segment_counts[intersect][segment1] -= 1
        intersect_segment_counts[intersect][segment2] -= 1
        if intersect_segment_counts[intersect].total() == 0:
            priority_queue.remove(
                (BOEvent.MEET, intersect),
                (intersect.x, BOEvent.MEET, intersect.y),
            )

    def insert_into_tree(segment):
        # type: (Segment) -> None
        segment_key = BOSegmentWrapper(segment)
        segment_wrappers[segment] = segment_key
        tree[segment_key] = segment
        # get neighbors
        neighbors = get_tree_neighbors(segment)
        # remove old intersects from the priority queue
        if len(neighbors) == 2:
            unschedule_intersect(*neighbors) # pylint: disable = no-value-for-parameter
        # insert new intersects into the priority queue (if not already inserted)
        for neighbor in neighbors:
            schedule_intersect(segment, neighbor)

    def remove_from_tree(segment):
        # type: (Segment) -> None
        # get neighbors
        neighbors = get_tree_neighbors(segment)
        # remove intersects from the priority queue
        for neighbor in neighbors:
            unschedule_intersect(segment, neighbor)
        # insert "uncovered" intersect from the priority queue
        if len(neighbors) == 2:
            schedule_intersect(*neighbors) # pylint: disable = no-value-for-parameter
        # remove from tree
        del tree[segment_wrappers[segment]]

    def swap(*segments):
        # type: (*Segment) -> None
        # arrange segments by decreasing slope, which correspond to bottom to top
        segments = tuple(sorted(
            segments,
            key=(lambda segment: (-segment.slope, segment)), # pylint: disable = superfluous-parens
        ))
        # manually update the SegmentWrappers to avoid floating point precision issues
        intersect = get_intersect(*segments[:2])
        steps = list(range(-len(segments) // 2, len(segments) // 2 + 1))
        if len(segments) % 2 == 0:
            steps.remove(0)
        for segment, step in zip(segments, steps):
            segment_wrappers[segment].y = nextafter(
                intersect.y,
                copysign(INF, step),
                steps=abs(step),
            )
        # update intersects with surrounding segments
        cursor_bot = tree.cursor(segment_wrappers[segments[0]])
        if cursor_bot.has_prev:
            segment_prev = cursor_bot.prev().value
            unschedule_intersect(segment_prev, segments[0])
            schedule_intersect(segment_prev, segments[-1])
        cursor_top = tree.cursor(segment_wrappers[segments[-1]])
        if cursor_top.has_next:
            segment_next = cursor_top.next().value
            unschedule_intersect(segments[-1], segment_next)
            schedule_intersect(segments[0], segment_next)
        # reverse the segments in the tree
        curr_cursor = cursor_bot
        for segment, step in zip(reversed(segments), steps):
            segment_wrappers[segment].y = nextafter(
                intersect.y,
                copysign(INF, step),
                steps=abs(step),
            )
            curr_cursor.node.key = segment_wrappers[segment]
            curr_cursor.node.value = segment
            if curr_cursor.has_next:
                curr_cursor = curr_cursor.next()

    def non_endpoint_intersect(intersect):
        # type: (Point2D) -> bool
        count = 0
        for segment in intersect_segment_counts[intersect]:
            if segment_intersect_map[segment][intersect]:
                count += 1
                if count == 2:
                    return True
        return False

    results = [] # type: list[Point2D]
    while priority_queue:
        (sweep_x, *_), (event_type, data) = priority_queue.pop()
        BOSegmentWrapper.sweep_x = sweep_x
        if event_type == BOEvent.START:
            assert isinstance(data, Segment)
            insert_into_tree(data)
        elif event_type == BOEvent.END:
            assert isinstance(data, Segment)
            remove_from_tree(data)
        elif event_type == BOEvent.MEET:
            assert isinstance(data, Point2D)
            intersect = data
            if include_end or non_endpoint_intersect(intersect):
                results.append(intersect)
            swap(*intersect_segment_counts[intersect])
    return results


class PointType(Enum):
    """Enum for point types."""
    LEAVE = 0
    MERGE = 1
    FLANK = 2
    SPLIT = 3
    ENTER = 4

    def __lt__(self, other):
        # type: (PointType) -> bool
        assert isinstance(other, PointType)
        return self.value < other.value

    def __gt__(self, other):
        # type: (PointType) -> bool
        assert isinstance(other, PointType)
        return self.value > other.value

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return self.name


class ClockDir(Enum):
    """Enum for clockwise directions."""
    DEASIL = -1
    WIDDER = 1

    def __repr__(self): # pragma: no cover
        # type: () -> str
        if self == ClockDir.DEASIL:
            return 'DEASIL'
        else:
            return 'WIDDER'


class WrappedPoint():
    """A wrapper around Point2D for polygon triangulation."""

    def __init__(self, point, polygon_index, point_index):
        # type: (Point2D, int, int) -> None
        """A wrapper around points of a polygon, to tell them apart."""
        self.point = point
        self.polygon_index = polygon_index
        self.point_index = point_index
        self.point_type = None # type: PointType
        self.deasil_point = None # type: WrappedPoint
        self.deasil_segment = None # type: Segment
        self.widder_point = None # type: WrappedPoint
        self.widder_segment = None # type: Segment
        self.posx_point = None # type: WrappedPoint

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'{self.polygon_index}:{self.point_index}:({self.point.x}, {self.point.y})'

    @property
    def x(self):
        # type: () -> float
        """Get the x-value of the point."""
        return self.point.x

    @property
    def y(self):
        # type: () -> float
        """Get the y-value of the point."""
        return self.point.y

    @property
    def mean_bearings(self):
        # type: () -> tuple[Optional[float], Optional[float]]
        """Calculate the mean "bearing" in the neg-x and pos-x directions."""
        # calculate segment bearings; flip the deasil segment so it's outwards from self
        deasil_bearing = self.deasil_segment.twin.bearing
        widder_bearing = self.widder_segment.bearing
        # calculate the mean bearing while dealing with the discontinuity
        mean_bearing = (deasil_bearing + widder_bearing) / 2
        if abs(deasil_bearing - widder_bearing) > PI:
            mean_bearing = mean_bearing - PI
        # determine which way the segments point
        has_negx = (self.deasil_point.x < self.x or self.widder_point.x < self.x)
        has_posx = (self.x < self.deasil_point.x or self.x < self.widder_point.x)
        # set the result depending on which way the segments point
        assert has_negx or has_posx
        result = (None, None) # type: tuple[Optional[float], Optional[float]]
        if has_negx and not has_posx:
            result = (mean_bearing, None)
        elif not has_negx and has_posx:
            result = (None, mean_bearing)
        elif self.deasil_point.x < self.x < self.widder_point.x:
            result = (deasil_bearing, widder_bearing)
        elif self.widder_point.x < self.x < self.deasil_point.x:
            result = (widder_bearing, deasil_bearing)
        else:
            assert False
        # convert results be smaller if neg-y and larger if pos-y
        assert result[0] is None or PI / 2 < result[0] < 3 * PI / 2, result
        assert result[1] is None or result[1] < PI / 2 or result[1] > 3 * PI / 2, result
        return (
            (None if result[0] is None else 3 * PI / 2 - result[0]),
            (None if result[1] is None else (result[1] + PI / 2) % (2 * PI)),
        )

    def get_dir_segment(self, clock_dir):
        # type: (ClockDir) -> Segment
        """Get the segment in either clock direction."""
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_segment
        else:
            return self.widder_segment

    @staticmethod
    def _compare_slopes(point1, point2):
        # type: (WrappedPoint, WrappedPoint) -> int
        """Compare the mean slopes of two points."""
        assert isinstance(point1, WrappedPoint)
        assert isinstance(point2, WrappedPoint)
        negx_mean_1, posx_mean_1 = point1.mean_bearings
        negx_mean_2, posx_mean_2 = point2.mean_bearings
        means = (negx_mean_1, posx_mean_1, negx_mean_2, posx_mean_2)
        if None not in means:
            assert (
                negx_mean_1 == negx_mean_2
                or posx_mean_1 == posx_mean_2
                or (
                    (negx_mean_1 < negx_mean_2) == (posx_mean_1 < posx_mean_2)
                    and (negx_mean_1 > negx_mean_2) == (posx_mean_1 > posx_mean_2)
                )
            ), means
            if negx_mean_1 < negx_mean_2 and posx_mean_1 <= posx_mean_2:
                return -1
            if negx_mean_1 <= negx_mean_2 and posx_mean_1 < posx_mean_2:
                return -1
            elif negx_mean_1 > negx_mean_2 and posx_mean_1 >= posx_mean_2:
                return 1
            elif negx_mean_1 >= negx_mean_2 and posx_mean_1 > posx_mean_2:
                return 1
            elif negx_mean_1 == negx_mean_2 and posx_mean_1 == posx_mean_2:
                return 0
            else:
                assert False
        elif None not in (negx_mean_1, negx_mean_2):
            if negx_mean_1 < negx_mean_2:
                return -1
            elif negx_mean_1 > negx_mean_2:
                return 1
            else:
                return 0
        elif None not in (posx_mean_1, posx_mean_2):
            if posx_mean_1 < posx_mean_2:
                return -1
            elif posx_mean_1 > posx_mean_2:
                return 1
            else:
                return 0
        else:
            assert negx_mean_1 is not None or posx_mean_1 is not None
            assert negx_mean_2 is not None or posx_mean_2 is not None
            # the two points are an ENTER and a LEAVE (or similar)
            # put the LEAVE second, which will have None as the posx_mean
            if posx_mean_1 is None:
                return 1
            if posx_mean_2 is None:
                return -1
            assert False, (point1, point2, means)


class WrappedPointPriority:
    """A comparison key for WrappedPoints, for the priority queue."""

    def __init__(self, point):
        # type: (WrappedPoint) -> None
        self.point = point

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, WrappedPointPriority)
            and self.point == other.point
        )

    def __lt__(self, other):
        # type: (WrappedPointPriority) -> bool
        assert isinstance(other, WrappedPointPriority)
        if self == other:
            return False
        if self.key != other.key:
            return self.key < other.key
        return WrappedPoint._compare_slopes(self.point, other.point) < 0

    def __gt__(self, other):
        # type: (WrappedPointPriority) -> bool
        assert isinstance(other, WrappedPointPriority)
        if self == other:
            return False
        if self.key != other.key:
            return self.key > other.key
        return WrappedPoint._compare_slopes(self.point, other.point) > 0

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'WrappedKey({self.point}, {self.point.point_type})'

    @property
    def key(self):
        # type: () -> tuple[float, float, PointType]
        """Return the comparison key."""
        return (self.point.x, self.point.y, self.point.point_type)


class Chain:
    """A chain of untriangulated points to the left of the sweep line."""

    def __init__(self, wrapped_points):
        # type: (WrappedPoint|Sequence[WrappedPoint]) -> None
        if isinstance(wrapped_points, WrappedPoint):
            self.points = [wrapped_points]
        else:
            self.points = list(wrapped_points)
        self.posx_index = 0

    def __len__(self):
        # type: () -> int
        return len(self.points)

    def __repr__(self): # pragma: no cover
        # type: () -> str
        args = ', '.join(repr(point) for point in self.points)
        return f'Chain({args})'

    @property
    def deasil_point(self):
        # type: () -> WrappedPoint
        """Get the next deasil point."""
        return self.points[0]

    @property
    def widder_point(self):
        # type: () -> WrappedPoint
        """Get the next widdershins point."""
        return self.points[-1]

    @property
    def deasil_key(self):
        # type: () -> ChainEnd
        """Get the deasil ChainEnd."""
        return ChainEnd(self, ClockDir.DEASIL)

    @property
    def widder_key(self):
        # type: () -> ChainEnd
        """Get the widder ChainEnd."""
        return ChainEnd(self, ClockDir.WIDDER)

    @property
    def posx_point(self):
        # type: () -> WrappedPoint
        """Get the "largest" point (with the highest positive x value)."""
        return self.points[self.posx_index]

    def get_dir_point(self, clock_dir):
        # type: (ClockDir) -> WrappedPoint
        """Get the end point in either clock direction."""
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_point
        else:
            return self.widder_point

    def get_dir_dir_point(self, clock_dir):
        # type: (ClockDir) -> WrappedPoint
        """Get the point past the end point in either clock direction."""
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_point.deasil_point
        else:
            return self.widder_point.widder_point

    def get_dir_pair(self, clock_dir):
        # type: (ClockDir) -> tuple[WrappedPoint, WrappedPoint]
        """Get the end two points in either clock direction.

        This always returns the points in widdershins order, which simplifies
        the triangle formation code.
        """
        if clock_dir == ClockDir.DEASIL:
            return self.points[0], self.points[1]
        else:
            return self.points[-2], self.points[-1]

    def get_dir_segment(self, clock_dir):
        # type: (ClockDir) -> Segment
        """Get the segment past the end point in either clock direction."""
        return self.get_dir_point(clock_dir).get_dir_segment(clock_dir)

    def get_dir_key(self, clock_dir):
        # type: (ClockDir) -> ChainEnd
        """Get the ChainEnd in either clock direction."""
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_key
        else:
            return self.widder_key

    def add_point(self, point, clock_dir):
        # type: (Chain, WrappedPoint, ClockDir) -> list[tuple[int, int, int]]
        """Add a point to the chain."""
        # define variables
        if clock_dir == ClockDir.DEASIL:
            end_index = 0
        else:
            end_index = -1
        # form all triangles possible
        triangles = []
        while len(self.points) > 1:
            # check if triangle is valid
            point1, point2 = self.get_dir_pair(clock_dir)
            if Segment.orientation(point1.point, point2.point, point.point) != -1:
                break
            assert len(set([point1.point_index, point2.point_index, point.point_index])) == 3
            triangles.append((point1.point_index, point2.point_index, point.point_index))
            self.points.pop(end_index)
        # add the new point to the chain
        if clock_dir == ClockDir.DEASIL:
            self.points.insert(0, point)
            self.posx_index = 0
        else:
            self.points.append(point)
            self.posx_index = len(self.points) - 1
        #self.validate()
        return triangles

    def interval_at(self, x):
        # type: (float) -> tuple[float, float]
        """Get the upper and lower bounds of the chain at the given x-value."""
        # calculate the slope of the adjacent segments, if not boxed in by other chains
        if self.deasil_point.deasil_point.x == self.deasil_point.x:
            deasil_slope = INF
            deasil_y = max(
                self.deasil_point.y,
                self.deasil_point.deasil_point.y,
            )
        else:
            deasil_slope = self.deasil_point.deasil_segment.slope
            deasil_y = self.deasil_point.y + deasil_slope * (x - self.deasil_point.x)
        if self.widder_point.widder_point.x == self.widder_point.x:
            widder_slope = INF
            widder_y = min(
                self.widder_point.y,
                self.widder_point.widder_point.y,
            )
        else:
            widder_slope = self.widder_point.widder_segment.slope
            widder_y = self.widder_point.y + widder_slope * (x - self.widder_point.x)
        assert deasil_y >= widder_y
        return deasil_y, widder_y

    def validate(self): # pragma: no cover
        # type: () -> None
        """Validate the chain."""
        # check the neg-x and pos-x pointers
        assert self.posx_point == max(
            self.points,
            key=(lambda point: point.point),
        )


class ChainEnd:
    """The end of a chain."""

    def __init__(self, chain, clock_dir):
        # type: (Chain, ClockDir) -> None
        """Initialize the ChainEnd."""
        assert isinstance(clock_dir, ClockDir)
        self.chain = chain
        self.clock_dir = clock_dir

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, ChainEnd)
            and self.chain == other.chain
            and self.clock_dir == other.clock_dir
        )

    def __lt__(self, other):
        # type: (Union[ChainEnd, WrappedPoint]) -> bool
        assert isinstance(other, (ChainEnd, WrappedPoint))
        #print('lt', self, other)
        if isinstance(other, ChainEnd):
            if self.chain == other.chain:
                #print('    lt 0.0', self.clock_dir == ClockDir.WIDDER and other.clock_dir == ClockDir.DEASIL)
                return self.clock_dir == ClockDir.WIDDER and other.clock_dir == ClockDir.DEASIL
            x = max(
                self.chain.deasil_point.x,
                self.chain.widder_point.x,
                other.chain.deasil_point.x,
                other.chain.widder_point.x,
            )
            self_interval = self.chain.interval_at(x)
            other_interval = other.chain.interval_at(x)
            #print(x, self_interval, other_interval)
            if self_interval != other_interval:
                #print('    lt 0.1', self_interval < other_interval)
                return self_interval < other_interval
            comparison = WrappedPoint._compare_slopes(self.point, other.point)
            #print('    lt 0.2', comparison < 0)
            return comparison < 0
        else:
            leaving = (
                self.chain.get_dir_dir_point(ClockDir.DEASIL) == other
                and self.chain.get_dir_dir_point(ClockDir.WIDDER) == other
            )
            if leaving:
                #print('    lt 0', self.clock_dir == ClockDir.WIDDER)
                return self.clock_dir == ClockDir.WIDDER
            if other == self.chain.get_dir_dir_point(self.clock_dir):
                #print('    lt 1', self.clock_dir == ClockDir.DEASIL)
                return self.clock_dir == ClockDir.DEASIL
            if other.point == self.chain.get_dir_point(self.clock_dir).point:
                comparison = WrappedPoint._compare_slopes(
                    self.chain.get_dir_point(self.clock_dir),
                    other,
                )
                #print('    lt 2', comparison < 0)
                return comparison < 0
            if other.point == self.chain.get_dir_dir_point(self.clock_dir).point:
                comparison = WrappedPoint._compare_slopes(
                    self.chain.get_dir_dir_point(self.clock_dir),
                    other,
                )
                #print('    lt 3', comparison < 0)
                return comparison < 0
            segment = self.chain.get_dir_segment(self.clock_dir)
            if segment.point1.x == segment.point2.x:
                #print('    lt 4', max(segment.point1.y, segment.point2.y) < other.y)
                return max(segment.point1.y, segment.point2.y) < other.y
            else:
                #print('    lt 5', segment.point_at(other.x).y < other.y)
                return segment.point_at(other.x).y < other.y

    def __gt__(self, other):
        # type: (Union[ChainEnd, WrappedPoint]) -> bool
        assert isinstance(other, (ChainEnd, WrappedPoint))
        #print('gt', self, other)
        if isinstance(other, ChainEnd):
            if self.chain == other.chain:
                #print('    gt 0.0', other.clock_dir == ClockDir.WIDDER and self.clock_dir == ClockDir.DEASIL)
                return other.clock_dir == ClockDir.WIDDER and self.clock_dir == ClockDir.DEASIL
            x = max(
                self.chain.deasil_point.x,
                self.chain.widder_point.x,
                other.chain.deasil_point.x,
                other.chain.widder_point.x,
            )
            self_interval = self.chain.interval_at(x)
            other_interval = other.chain.interval_at(x)
            #print(x, self_interval, other_interval)
            if self_interval != other_interval:
                #print('    gt 0.1', self_interval > other_interval)
                return self_interval > other_interval
            comparison = WrappedPoint._compare_slopes(self.point, other.point)
            #print('    gt 0.2', comparison > 0)
            return comparison > 0
        else:
            leaving = (
                self.chain.get_dir_dir_point(ClockDir.DEASIL) == other
                and self.chain.get_dir_dir_point(ClockDir.WIDDER) == other
            )
            if leaving:
                #print('    gt 0', self.clock_dir == ClockDir.DEASIL)
                return self.clock_dir == ClockDir.DEASIL
            if other == self.chain.get_dir_dir_point(self.clock_dir):
                #print('    gt 1', self.clock_dir == ClockDir.WIDDER)
                return self.clock_dir == ClockDir.WIDDER
            if other.point == self.chain.get_dir_point(self.clock_dir).point:
                comparison = WrappedPoint._compare_slopes(
                    self.chain.get_dir_point(self.clock_dir),
                    other,
                )
                #print('    gt 2', comparison > 0)
                return comparison > 0
            if other.point == self.chain.get_dir_dir_point(self.clock_dir).point:
                comparison = WrappedPoint._compare_slopes(
                    self.chain.get_dir_dir_point(self.clock_dir),
                    other,
                )
                #print('    gt 3', comparison > 0)
                return comparison > 0
            segment = self.chain.get_dir_segment(self.clock_dir)
            if segment.point1.x == segment.point2.x:
                #print('    gt 4', max(segment.point1.y, segment.point2.y) > other.y)
                return max(segment.point1.y, segment.point2.y) > other.y
            else:
                #print('    gt 5', segment.point_at(other.x).y > other.y)
                return segment.point_at(other.x).y > other.y

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'ChainEnd({self.point} {self.clock_dir} {self.chain})'

    @property
    def point(self):
        # type: () -> WrappedPoint
        """Get the point represented by this ChainEnd."""
        return self.chain.get_dir_point(self.clock_dir)


class Chains:
    """A class to manage the chains."""

    def __init__(self):
        # type: () -> None
        self.tree = SortedDict() # type: SortedDict[ChainEnd, Chain]
        self.triangles = [] # type: list[tuple[int, int, int]]

    def create_chain(self, point):
        # type: (WrappedPoint) -> Chain
        """Create a chain."""
        chain = Chain(point)
        self.add_chain(chain)
        return chain

    def add_chain(self, chain):
        # type: (Chain) -> None
        """Add a chain to the data structures."""
        self.tree[chain.deasil_key] = chain
        self.tree[chain.widder_key] = chain

    def extend_chain(self, chain, point, clock_dir):
        # type: (Chain, WrappedPoint, ClockDir) -> None
        """Extend a chain with a point.

        This function will continue down adjacent chains if appropriate.
        """
        assert chain is not None
        self.remove_chain(chain)
        self.triangles.extend(chain.add_point(point, clock_dir))
        # decide whether to reinsert the chain
        if not (len(chain) == 2 and chain.deasil_point.deasil_point == chain.widder_point):
            # if the chain is not the last one due to a LEAVE point
            # it is curving away and need to be reinserted
            self.add_chain(chain)
        #chain.validate()

    def remove_chain(self, chain):
        # type: (Chain) -> None
        """Remove a chain from the chains data structure."""
        del self.tree[chain.get_dir_key(ClockDir.DEASIL)]
        del self.tree[chain.get_dir_key(ClockDir.WIDDER)]

    def merge_chains_at(self, point):
        # type: (WrappedPoint) -> None
        """Merge two chains by joining them at the given point."""
        deasil_chain, widder_chain = self.get_nearest_chains(point)
        assert deasil_chain.widder_point.widder_point == point
        assert widder_chain.deasil_point.deasil_point == point
        self.remove_chain(deasil_chain)
        self.remove_chain(widder_chain)
        deasil_chain_length = len(deasil_chain)
        self.triangles.extend(deasil_chain.add_point(point, ClockDir.WIDDER))
        self.triangles.extend(widder_chain.add_point(point, ClockDir.DEASIL))
        deasil_chain.points.extend(widder_chain.points[1:])
        if widder_chain.posx_point.point > deasil_chain.posx_point.point:
            deasil_chain.posx_index = deasil_chain_length + widder_chain.posx_index
        self.add_chain(deasil_chain)

    def get_nearest_chains(self, point):
        # type: (WrappedPoint) -> tuple[Optional[Chain], Optional[Chain]]
        """Get the chains above and below a point.

        Since the sorting puts smaller y-values first, we need to flip the order
        that things are returned to put them in deasil/widdershins order.
        """
        assert isinstance(point, WrappedPoint)
        prev_cursor, next_cursor = self.tree.bracket(point)
        return (
            next_cursor.value if next_cursor else None,
            prev_cursor.value if prev_cursor else None,
        )

    def validate(self): # pragma: no cover
        # type: () -> None
        """Validate the chain."""
        keys = []
        for i, (key, chain) in enumerate(self.tree.items()):
            if i % 2 == 0:
                assert key.clock_dir == ClockDir.WIDDER
            else:
                assert key.clock_dir == ClockDir.DEASIL
            assert key.chain == chain
            assert key in (chain.deasil_key, chain.widder_key), (key, chain.deasil_key, chain.widder_key)
            assert chain.deasil_key in self.tree, chain.deasil_key
            assert chain.widder_key in self.tree, chain.widder_key
            chain.validate()
            keys.append(key)
        for i, key1 in enumerate(keys):
            for key2 in keys[i + 1:]:
                assert key1 != key2
                assert (key1 < key2) == (key2 > key1), (key1, key2)
                if key1 < key2:
                    assert not key2 < key1, (key1, key2)
                else:
                    assert key2 < key1, (key1, key2)
                if key2 < key1:
                    assert not key1 < key2, (key1, key2)
                else:
                    assert key1 < key2, (key1, key2)


def _preprocess_points(polygon_index, points):
    # type: (int, Sequence[Point2D]) -> list[WrappedPoint]
    segments = [
        Segment(points[i], points[i + 1])
        for i in range(-1, len(points) - 1)
    ]
    segments.append(segments[0])
    wrapped_points = [
        WrappedPoint(point, polygon_index, index)
        for index, point in enumerate(points)
    ]
    wrapped_points[0].deasil_point = wrapped_points[-1]
    wrapped_points[-1].widder_point = wrapped_points[0]
    for wrapped_point in wrapped_points:
        deasil_point = wrapped_point.deasil_point
        widder_point = wrapped_points[(wrapped_point.point_index + 1) % len(points)]
        wrapped_point.widder_point = widder_point
        widder_point.deasil_point = wrapped_point
        if deasil_point.point < wrapped_point.point:
            wrapped_point.posx_point = widder_point
        else:
            wrapped_point.posx_point = deasil_point
        deasil_segment = segments[wrapped_point.point_index]
        widder_segment = segments[wrapped_point.point_index + 1]
        wrapped_point.deasil_segment = deasil_segment
        wrapped_point.widder_segment = widder_segment
        wrapped_point.point_type = PointType.FLANK
        orientation = Segment.orientation(
            deasil_point.point,
            wrapped_point.point,
            widder_point.point,
        )
        if deasil_point.point > wrapped_point.point and widder_point.point > wrapped_point.point:
            if orientation == -1:
                wrapped_point.point_type = PointType.ENTER
            elif orientation == 1:
                wrapped_point.point_type = PointType.SPLIT
        elif deasil_point.point < wrapped_point.point and widder_point.point < wrapped_point.point:
            if orientation == -1:
                wrapped_point.point_type = PointType.LEAVE
            elif orientation == 1:
                wrapped_point.point_type = PointType.MERGE
    return wrapped_points


def triangulate_polygon(points):
    # type: (Sequence[Point2D]) -> tuple[tuple[int, int, int], ...]
    """Triangulate a simple polygon.

    This is an overly-complicated implementation of monotone polygon
    triangulation. The complications include:

    * Doing the monotone partitioning and the triangulation in a single pass
    * Allowing vertical perimeter segments 
    * Allowing polygons with holes (ie. that are not simple)
    * Allowing polygons whose perimeter visit a point multiple times

    An explicit non-goal is dealing with polygons with zero-width interiors,
    which would allow polygons that are disconnected. Zero-width exteriors are
    allowed, as per the standard trick for representing a polygon with holes
    (by connecting the hole to the perimeter with a zero-width "gap".)

    The standard monotone triangulation algorithm uses a sweep-line (this
    implementation goes from negative-x to positive-x) and maintains "chains"
    of untriangulated point behind the line. To deal with vertical segments,
    points with the same x but a more negative y are processed first. The
    chains are kept in a sorted data structure ordered by their vertical
    position, such that as new points are encountered, the relevant chain can
    be found and updated. Because this implementation partitions at the same
    time as it triangulates, the chains are more complicated; notably, they may
    not be monotonic in y, or be classifiable into the "top" or "bottom" of the
    polygon. Instead, a chain should be thought of as all untriangulated points
    behind the sweep line, ordered (counter-)clockwise, and bounded above and
    below by segments that extend ahead of the sweep line. Each chain also
    tracks it's most positive-x point, where the chain could be split (where
    the polygon would have been partitioned into monotone components).

    Managing the complications listed above is, in practice, a matter of
    defining sorting order of the chains consistently. At a high level,
    as with the standard algorithm, the chains are sorted vertically by the
    area (or interval at the sweep line position) defined by the two boundary
    segments.  Since the same point could be on the perimeter multiple times,
    however, care must be taken to determine which vertex is being processed,
    and to maintain the sorting order despite having the same coordinate. The
    solution is to use the slopes of the segments before and after the point,
    reminiscent of similar comparisons in the Bentley-Ottman all intersections
    algorithm. The details of the sorting can be found in the __lt__ and __gt__
    methods of the ChainEnd class.

    References:

    * Polygon Triangulation on Wikipedia
      https://en.wikipedia.org/wiki/Polygon_triangulation
    * Lecture notes by David Mount
      https://www.cs.umd.edu/users/mount/
    * Hertel and Mehlhorn (1985). Fast Triangulation of the Plane with Respect
      to Simple Polygons.
    """

    # initialize sweep line variables
    priority_queue = PriorityQueue(key=WrappedPointPriority) # type: PriorityQueue[WrappedPointPriority, WrappedPoint]
    chains = Chains()
    for point in _preprocess_points(0, points):
        if point.point_type in (PointType.ENTER, PointType.SPLIT):
            priority_queue.push(point)
    # start the sweep line
    visited = set()
    assert priority_queue.peek()[1].point_type == PointType.ENTER, points
    while priority_queue:
        # get the next point from the priority queue
        _, point = priority_queue.pop()
        # need to check if the point has already been visited
        # since a point could be added both initial and after a FLANK point
        if point in visited:
            continue
        visited.add(point)
        #print(f'\n{point} {point.point_type}')
        #print(point.deasil_point, '->', point, '->', point.widder_point)
        # process the point
        if point.point_type == PointType.ENTER:
            chains.create_chain(point)
        elif point.point_type == PointType.LEAVE:
            deasil_chain, widder_chain = chains.get_nearest_chains(point)
            assert deasil_chain and widder_chain and deasil_chain == widder_chain
            assert deasil_chain.widder_point.widder_point == point
            assert widder_chain.deasil_point.deasil_point == point
            chains.extend_chain(deasil_chain, point, ClockDir.WIDDER)
        elif point.point_type == PointType.SPLIT:
            deasil_chain, widder_chain = chains.get_nearest_chains(point)
            assert deasil_chain and widder_chain and deasil_chain == widder_chain
            chain = deasil_chain
            chains.remove_chain(chain)
            new_deasil_chain = Chain(chain.points[:chain.posx_index+1])
            new_widder_chain = Chain(chain.points[chain.posx_index:])
            # need to add the chains carefully to trigger the asserts
            chains.triangles.extend(new_deasil_chain.add_point(point, ClockDir.WIDDER))
            chains.triangles.extend(new_widder_chain.add_point(point, ClockDir.DEASIL))
            chains.add_chain(new_deasil_chain)
            chains.add_chain(new_widder_chain)
        elif point.point_type == PointType.MERGE:
            chains.merge_chains_at(point)
        else:
            deasil_chain, widder_chain = chains.get_nearest_chains(point)
            if point.posx_point == point.widder_point:
                chains.extend_chain(
                    deasil_chain,
                    point,
                    ClockDir.WIDDER,
                )
            else:
                chains.extend_chain(
                    widder_chain,
                    point,
                    ClockDir.DEASIL,
                )
        if point.deasil_point.point > point.point:
            priority_queue.push(point.deasil_point)
        if point.widder_point.point > point.point:
            priority_queue.push(point.widder_point)
        #chains.validate()
        #_print_chains(chains)
        #_visualize_state(points, chains)
    return tuple(chains.triangles)


BearingInfo = namedtuple('BearingInfo', 'prev_index, bearing, next_index')


def convex_partition(points, triangle_indices=None):
    # type: (Sequence[Point2D], Sequence[tuple[int, int, int]]) -> tuple[tuple[int, ...], ...]
    """Partition a simple polygon into component convex polygons."""
    # get triangulation indices
    if triangle_indices is None:
        triangle_indices = triangulate_polygon(points)
    # set up data structures
    point_bearings_map = defaultdict(dict) # type: dict[int, dict[int, BearingInfo]]
    bearings = {} # type: dict[tuple[int, int], float]
    interior_segments = set() # type: set[tuple[int, int]]
    for triangle_index in triangle_indices:
        shifted_index = triangle_index[1:] + (triangle_index[0],)
        for index1, index2 in zip(triangle_index, shifted_index):
            point_bearings_map[index1][index2] = None
            point_bearings_map[index2][index1] = None
            segment = Segment(points[index1], points[index2])
            bearings[(index1, index2)] = segment.bearing
            if segment.bearing > PI:
                bearings[(index2, index1)] = segment.bearing - PI
            else:
                bearings[(index2, index1)] = segment.bearing + PI
            if abs(index1 - index2) not in (1, len(points) - 1):
                if index1 < index2:
                    interior_segments.add((index1, index2))
                else:
                    interior_segments.add((index2, index1))
    # for every point, create a linked list of neighbors ordered by bearing
    for index1 in range(len(points)):
        # store bearings of all connected points as a linked structure
        point_bearings = sorted(
            (bearings[(index1, index2)], index2)
            for index2 in point_bearings_map[index1]
        )
        point_bearings_map[index1] = {}
        for i, (bearing, index2) in enumerate(point_bearings):
            point_bearings_map[index1][index2] = BearingInfo(
                point_bearings[(i - 1) % len(point_bearings)][1],
                bearing,
                point_bearings[(i + 1) % len(point_bearings)][1],
            )
    # repeatedly remove non-essential segments until there are no more changes
    changed_segments = set(interior_segments)
    while changed_segments:
        new_changed_segments = set()
        for index1, index2 in changed_segments:
            if index2 not in point_bearings_map[index1]:
                continue
            # segment is essential if at least one end is dividing a reflex angle
            essential = False
            for src_index, dst_index in ((index1, index2), (index2, index1)):
                point_info = point_bearings_map[src_index]
                angle_info = point_info[dst_index]
                angle = (
                    point_info[angle_info.next_index].bearing
                    - point_info[angle_info.prev_index].bearing
                ) % (2 * PI)
                if angle >= PI:
                    essential = True
                    break
            if essential:
                continue
            # update the bearings data structure
            for src_index, dst_index in ((index1, index2), (index2, index1)):
                point_info = point_bearings_map[src_index]
                # remove the segment from the chain
                bearing_info = point_info[dst_index]
                prev_index = bearing_info.prev_index
                next_index = bearing_info.next_index
                point_info[prev_index] = point_info[prev_index]._replace(
                    next_index=next_index,
                )
                point_info[next_index] = point_info[next_index]._replace(
                    prev_index=prev_index,
                )
                # add adjacent segments as having changed
                for other_index in (prev_index, next_index):
                    key = (src_index, other_index)
                    if key in interior_segments:
                        new_changed_segments.add(key)
            del point_bearings_map[index1][index2]
            del point_bearings_map[index2][index1]
        changed_segments = new_changed_segments
    # create the index lists of convex partitions via breadth-first search
    frontier = [(0, 1),]
    visited = set()
    convex_indices = []
    while frontier:
        curr_index, next_index = frontier.pop(0)
        init_index = curr_index
        if (curr_index, next_index) in visited:
            continue
        visited.add((curr_index, next_index))
        face_indices = [curr_index]
        while next_index != init_index:
            next_next_index = point_bearings_map[next_index][curr_index].prev_index
            curr_index = next_index
            next_index = next_next_index
            face_indices.append(curr_index)
            visited.add((curr_index, next_index))
            add_twin = (
                (next_index, curr_index) not in visited
                and abs(next_index - curr_index) not in (1, len(points) - 1)
            )
            if add_twin:
                frontier.append((next_index, curr_index))
        convex_indices.append(tuple(face_indices))
    return tuple(convex_indices)
