"""Utility algorithms."""

from collections import defaultdict, Counter
from collections.abc import Sequence
from enum import IntEnum, Enum
from math import inf as INF, copysign, nextafter
from typing import Any, Optional, Union

from .data_structures import SortedDict, PriorityQueue
from .simplex import Point2D, Segment


class _SegmentWrapper:
    """A wrapper class for ordering Segments in sweep line algorithms."""

    sweep_x = None # type: float

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

    def __repr__(self):
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
        assert isinstance(other, PointType)
        return self.value < other.value

    def __gt__(self, other):
        assert isinstance(other, PointType)
        return self.value > other.value

    def __repr__(self):
        # type: () -> str
        return self.name


class ClockDir(Enum):
    """Enum for clockwise directions."""
    DEASIL = -1
    WIDDER = 1

    @property
    def opposite(self):
        # type: () -> ClockDir
        """The opposite direction."""
        if self == ClockDir.DEASIL:
            return ClockDir.WIDDER
        else:
            return ClockDir.DEASIL

    def __repr__(self):
        # type: () -> str
        if self == ClockDir.DEASIL:
            return 'DEASIL'
        else:
            return 'WIDDER'


class WrappedPoint():

    def __init__(self, point, index):
        """A wrapper around points of a polygon, to tell them apart."""
        self.point = point
        self.index = index
        self.point_type = None # type: str
        self.deasil_point = None # type: WrappedPoint
        self.deasil_segment = None # type: Segment
        self.widder_point = None # type: WrappedPoint
        self.widder_segment = None # type: Segment
        self.negx_point = None # type: WrappedPoint
        self.nposx_point = None # type: WrappedPoint
        self.negx_slope = 0 # type: float
        self.posx_slope = 0 # type: float

    @property
    def x(self):
        return self.point.x

    @property
    def y(self):
        return self.point.y

    def get_dir_point(self, clock_dir):
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_point
        else:
            return self.widder_point

    def get_dir_segment(self, clock_dir):
        # FIXME may be able to replace this with get_dir_slope
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_segment
        else:
            return self.widder_segment

    def __repr__(self):
        return f'{self.index}:({self.point.x}, {self.point.y})'


class Chain:
    """A chain of untriangulated points to the left of the sweep line.

    FIXME Chains are (non-strictly) monotonic; for all adjacent points p and q, either:

    * (p.x <= q.x and p.y <= q.y)
    * or (p.x < q.x and p.y >= q.y)

    In particular, as a chain grows in the pos-x direction, it can only go up a
    vertical segment.
    """

    def __init__(self, wrapped_point):
        self.points = [wrapped_point]
        self.negx_point = wrapped_point
        self.posx_point = wrapped_point
        self.deasil_chain = None # type: Chain
        self.widder_chain = None # type: Chain

    def __len__(self):
        return len(self.points)

    @property
    def deasil_point(self):
        # type: () -> WrappedPoint
        return self.points[0]

    @property
    def widder_point(self):
        # type: () -> WrappedPoint
        return self.points[-1]

    @property
    def deasil_key(self):
        return ChainEnd(self, ClockDir.DEASIL)

    @property
    def widder_key(self):
        # type: () -> ChainEnd
        return ChainEnd(self, ClockDir.WIDDER)

    def get_dir_point(self, direction):
        # type: (ClockDir) -> WrappedPoint
        if direction == ClockDir.DEASIL:
            return self.deasil_point
        else:
            return self.widder_point

    def get_dir_pair(self, direction):
        # type: (ClockDir) -> tuple[WrappedPoint, WrappedPoint]
        if direction == ClockDir.DEASIL:
            return self.points[0], self.points[1]
        else:
            return self.points[-2], self.points[-1]

    def get_dir_key(self, direction):
        # type: (ClockDir) -> ChainEnd
        if direction == ClockDir.DEASIL:
            return self.deasil_key
        else:
            return self.widder_key

    def set_dir_chain(self, clock_dir, chain):
        if clock_dir == ClockDir.DEASIL:
            self.deasil_chain = chain
        else:
            self.widder_chain = chain

    def get_dir_chain(self, clock_dir):
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_chain
        else:
            return self.widder_chain

    def trim_dir(self, direction):
        # type: (ClockDir) -> WrappedPoint
        if direction == ClockDir.DEASIL:
            result = self.points[0]
            self.points = self.points[1:]
            backup_point = self.points[0]
        else:
            result = self.points[-1]
            self.points = self.points[:-1]
            backup_point = self.points[-1]
        if result == self.posx_point:
            self.posx_point = backup_point
        else:
            self.negx_point = backup_point
        #self.validate_x_points()
        return result

    def is_valid_add_point(self, point, direction):
        return point.point > self.get_dir_point(direction).point

    def add_point(self, point, direction):
        # type: (Chain, WrappedPoint, ClockDir) -> list[tuple[int, int, int]]
        # form all triangles possible
        triangles = []
        while len(self.points) > 1:
            point1, point2 = self.get_dir_pair(direction)
            if Segment.orientation(point1.point, point2.point, point.point) != -1:
                break
            assert len(set([point1.index, point2.index, point.index])) == 3
            triangles.append((point1.index, point2.index, point.index))
            self.trim_dir(direction)
        # update the chain
        if direction == ClockDir.DEASIL:
            self.points.insert(0, point)
            if self.deasil_chain:
                self.deasil_chain.widder_chain = None
                self.deasil_chain = None
        else:
            self.points.append(point)
            if self.widder_chain:
                self.widder_chain.deasil_chain = None
                self.widder_chain = None
        if point.point > self.posx_point.point:
            self.posx_point = point
        else:
            self.negx_point = point
        #self.validate_x_points()
        #self.validate()
        return triangles

    def __repr__(self):
        points = [f'{point.index}:({point.x}, {point.y})' for point in self.points]
        return f'Chain({", ".join(points)})'

    def interval_at(self, x):
        deasil_deasil_point = self.deasil_point.deasil_point
        if deasil_deasil_point.x > self.deasil_point.x and deasil_deasil_point.x >= x:
            deasil_slope = self.deasil_point.deasil_segment.slope
        else:
            deasil_slope = 0
        widder_widder_point = self.widder_point.widder_point
        if widder_widder_point.x > self.widder_point.x and widder_widder_point.x >= x:
            widder_slope = self.widder_point.widder_segment.slope
        else:
            widder_slope = 0
        result = (
            self.deasil_point.y + deasil_slope * (x - self.deasil_point.x),
            self.widder_point.y + widder_slope * (x - self.widder_point.x),
        )
        # check if we've gone past the intersection point, in which case just
        # use the y-values
        # FIXME assert result[0] >= result[1], (x, result, self, deasil_slope, widder_slope)
        if result[0] < result[1]:
            return self.deasil_point.y, self.widder_point.y
        else:
            return result

    def validate_x_points(self):
        assert self.posx_point == max(
            self.points,
            key=(lambda point: point.point),
        )
        assert self.negx_point == min(
            self.points,
            key=(lambda point: point.point),
        )

    def validate(self):
        assert self.widder_key < self.deasil_key, (self, self.deasil_key, self.widder_key)
        if self.deasil_chain:
            assert self.deasil_chain.widder_point == self.deasil_point
        if self.widder_chain:
            assert self.widder_chain.deasil_point == self.widder_point


class ChainEnd:

    def __init__(self, chain, clock_dir):
        """Initialize the ChainEnd."""
        assert isinstance(clock_dir, ClockDir)
        self.chain = chain
        self.clock_dir = clock_dir

    def __eq__(self, other):
        return (
            isinstance(other, ChainEnd)
            and self.chain == other.chain
            and self.clock_dir == other.clock_dir
        )

    def __lt__(self, other):
        assert isinstance(other, (ChainEnd, WrappedPoint))
        if isinstance(other, ChainEnd):
            if self.chain == other.chain:
                return self.clock_dir == ClockDir.WIDDER and other.clock_dir == ClockDir.DEASIL
            # FIXME need to determine if self.chain < other.chain
            x = max(
                self.chain.deasil_point.x,
                self.chain.widder_point.x,
                other.chain.deasil_point.x,
                other.chain.widder_point.x,
            )
            self_interval = self.chain.interval_at(x)
            other_interval = other.chain.interval_at(x)
            return self_interval < other_interval
        else:
            if self.point == other:
                if len(self.chain) == 1:
                    return self.clock_dir == ClockDir.WIDDER
                else:
                    return self.clock_dir == ClockDir.DEASIL
            assert (
                (
                    other.x >= self.chain.deasil_point.x 
                    and other.x >= self.chain.widder_point.x
                )
                or other in (self.chain.deasil_point, self.chain.widder_point)
                or (
                    other.y <= self.chain.deasil_point.y 
                    and other.y <= self.chain.widder_point.y
                ) or (
                    other.y >= self.chain.deasil_point.y 
                    and other.y >= self.chain.widder_point.y
                )
            )
            # if they are the opposite end, the only way we can be lesser is
            # if we are the widder end
            if other == self.chain.negx_point:
                return self.clock_dir == ClockDir.WIDDER
            if other.x >= self.chain.posx_point.x:
                interval = self.chain.interval_at(other.x)
                if self.clock_dir == ClockDir.DEASIL:
                    return interval[0] < other.y
                else:
                    return interval[1] < other.y
            else:
                return (
                    self.chain.deasil_point.y <= other.y
                    and self.chain.widder_point.y <= other.y
                )

    def __gt__(self, other):
        assert isinstance(other, (ChainEnd, WrappedPoint))
        if isinstance(other, ChainEnd):
            if self.chain == other.chain:
                return other.clock_dir == ClockDir.WIDDER and self.clock_dir == ClockDir.DEASIL
            x = max(
                self.chain.deasil_point.x,
                self.chain.widder_point.x,
                other.chain.deasil_point.x,
                other.chain.widder_point.x,
            )
            self_interval = self.chain.interval_at(x)
            other_interval = other.chain.interval_at(x)
            return self_interval > other_interval
        else:
            if self.point == other:
                if len(self.chain) == 1:
                    return self.clock_dir == ClockDir.DEASIL
                else:
                    return self.clock_dir == ClockDir.WIDDER
            assert (
                (
                    other.x >= self.chain.deasil_point.x 
                    and other.x >= self.chain.widder_point.x
                )
                or other == self.chain.negx_point
                or (
                    other.y <= self.chain.deasil_point.y 
                    and other.y <= self.chain.widder_point.y
                ) or (
                    other.y >= self.chain.deasil_point.y 
                    and other.y >= self.chain.widder_point.y
                )
            )
            # if they are the opposite end, the only way we can be greater is
            # if we are the deasil end
            if other == self.chain.negx_point:
                return self.clock_dir == ClockDir.DEASIL
            if other.x >= self.chain.posx_point.x:
                interval = self.chain.interval_at(other.x)
                if self.clock_dir == ClockDir.DEASIL:
                    return interval[0] > other.y
                else:
                    return interval[1] > other.y
            else:
                return (
                    self.chain.deasil_point.y >= other.y
                    and self.chain.widder_point.y >= other.y
                )

    def __repr__(self):
        return f'ChainEnd({self.point} {self.slope} {self.clock_dir} {self.chain})'

    @property
    def point(self):
        return self.chain.get_dir_point(self.clock_dir)

    @property
    def x(self):
        return self.point.x

    @property
    def y(self):
        return self.point.y

    @property
    def slope(self):
        if self.point.get_dir_point(self.clock_dir).x > self.x:
            return self.point.get_dir_segment(self.clock_dir).slope
        else:
            return 0

    def _y_at(self, x):
        assert x >= self.x
        return self.y + self.slope * (x - self.x)


class Chains:

    def __init__(self):
        self.chains = set() # FIXME unnecessary variable
        self.tree = SortedDict() # type: dict[ChainEnd, Chain]
        self.point_chain_map = {}

    def __len__(self):
        return len(self.chains)

    def __iter__(self):
        yielded = set()
        for chain in self.tree.values():
            if chain not in yielded:
                yield chain
                yielded.add(chain)

    def items(self):
        yield from self.tree.items()

    def create_chain(self, point):
        # type: () -> Chain
        chain = Chain(point)
        self.add_chain(chain)
        return chain

    def add_chain(self, chain):
        self.chains.add(chain)
        assert (chain.deasil_point, ClockDir.WIDDER) not in self.point_chain_map
        self.point_chain_map[(chain.deasil_point, ClockDir.WIDDER)] = chain
        assert (chain.widder_point, ClockDir.DEASIL) not in self.point_chain_map
        self.point_chain_map[(chain.widder_point, ClockDir.DEASIL)] = chain
        self.tree[chain.deasil_key] = chain
        self.tree[chain.widder_key] = chain

    def extend_chain(self, chain, point, direction):
        # type: (Chain, WrappedPoint, ClockDir) -> list[tuple[int, int, int]]
        """Extend a chain with a point.

        This function will continue down adjacent chains if appropriate.
        """
        assert chain is not None
        triangles =  []
        while chain:
            del self.point_chain_map[(chain.get_dir_point(direction), direction.opposite)]
            del self.point_chain_map[(chain.get_dir_point(direction.opposite), direction)]
            del self.tree[chain.get_dir_key(direction)]
            del self.tree[chain.get_dir_key(direction.opposite)]
            if chain.is_valid_add_point(point, direction):
                triangles.extend(chain.add_point(point, direction))
            next_chain = chain.get_dir_chain(direction.opposite)
            if len(chain) == 2 and next_chain and next_chain.get_dir_point(direction).point_type != PointType.SPLIT:
                self.chains.remove(chain)
                prev_chain = chain.get_dir_chain(direction)
                next_chain = chain.get_dir_chain(direction.opposite)
                if prev_chain:
                    prev_chain.set_dir_chain(direction.opposite, next_chain)
                next_chain.set_dir_chain(direction, prev_chain)
                chain = next_chain
            else:
                assert (chain.get_dir_point(direction), direction.opposite) not in self.point_chain_map
                self.point_chain_map[(chain.get_dir_point(direction), direction.opposite)] = chain
                self.point_chain_map[(chain.get_dir_point(direction.opposite), direction)] = chain
                self.tree[chain.get_dir_key(direction)] = chain
                self.tree[chain.get_dir_key(direction.opposite)] = chain
                chain.validate()
                break
        return triangles

    def delete_chain(self, chain):
        deasil_chain = self.tree[chain.deasil_key]
        widder_chain = self.tree[chain.widder_key]
        assert chain == deasil_chain == widder_chain
        del self.tree[chain.deasil_key]
        del self.tree[chain.widder_key]
        del self.point_chain_map[(chain.deasil_point, ClockDir.WIDDER)]
        del self.point_chain_map[(chain.widder_point, ClockDir.DEASIL)]
        if chain.deasil_chain:
            chain.deasil_chain.widder_chain = None
        if chain.widder_chain:
            chain.widder_chain.deasil_chain = None
        self.chains.remove(chain)

    def get_encompassing_chains(self, point):
        # type: (Point2D) -> tuple[Optional[Chain], Optional[Chain]]
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

    def get_chain_at(self, point, clock_dir):
        """Get a chain at the specified point.

        The clock_dir argument specifies the direction to look for the
        chain, NOT the end. So a clock_dir of WIDDER would return a ChainEnd
        with clock_dir==DEASIL
        """
        return self.point_chain_map[(point, clock_dir)]

    def validate(self):
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
            assert (chain.deasil_point, ClockDir.WIDDER) in self.point_chain_map
            assert (chain.widder_point, ClockDir.DEASIL) in self.point_chain_map
            '''
            # not true when merging multiple times
            assert (
                chain.deasil_point.x < chain.deasil_point.deasil_point.x
                or chain.widder_point.x < chain.widder_point.widder_point.x
            )
            '''
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

def _preculculate_points_info(points):
    segments = [
        Segment(points[i], points[i + 1])
        for i in range(-1, len(points) - 1)
    ]
    segments.append(segments[0])
    wrapped_points = [
        WrappedPoint(point, index)
        for index, point in enumerate(points)
    ]
    wrapped_points[0].deasil_point = wrapped_points[-1]
    wrapped_points[-1].widder_point = wrapped_points[0]
    for wrapped_point in wrapped_points:
        deasil_point = wrapped_point.deasil_point
        widder_point = wrapped_points[(wrapped_point.index + 1) % len(points)]
        wrapped_point.widder_point = widder_point
        widder_point.deasil_point = wrapped_point
        if deasil_point.point < wrapped_point.point:
            wrapped_point.negx_point = deasil_point
            wrapped_point.posx_point = widder_point
        else:
            wrapped_point.negx_point = widder_point
            wrapped_point.posx_point = deasil_point
        deasil_segment = segments[wrapped_point.index]
        widder_segment = segments[wrapped_point.index + 1]
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
            wrapped_point.negx_slope = None
            wrapped_point.posx_slope = (deasil_segment.slope + widder_segment.slope) / 2
        elif deasil_point.point < wrapped_point.point and widder_point.point < wrapped_point.point:
            if orientation == -1:
                wrapped_point.point_type = PointType.LEAVE
            elif orientation == 1:
                wrapped_point.point_type = PointType.MERGE
            wrapped_point.negx_slope = (deasil_segment.slope + widder_segment.slope) / -2
            wrapped_point.posx_slope = None
        else:
            if deasil_point.point < wrapped_point.point:
                wrapped_point.negx_slope = deasil_segment.slope
                wrapped_point.posx_slope = widder_segment.slope
            else:
                wrapped_point.negx_slope = widder_segment.slope
                wrapped_point.posx_slope = deasil_segment.slope
    return wrapped_points


def triangulate_polygon(points):
    # type: (Sequence[Point2D]) -> tuple[tuple[int, int, int], ...]
    """Triangulate a simple polygon.

    This is an overly-complicated implementation of monotone polygon
    triangularization. This (pre-complication) implementation is based on the
    lecture notes by David Mount at the University of Maryland. The primary
    complication comes from doing the monotone partitioning and the
    triangularization itself in one sweep, in addition to dealing with vertical
    segments. Instead of sorting points by their y-values - which could cause
    points to be processed without being connected to a chain - the queue for
    the main loop is initialized with only start and split points, with other
    points added as the points to the left are processed. This forces points in
    a vertical line to be processed in increasing distance from points to the
    left, forming a chain. Nonetheless, as a tiebreaker, points with a smaller
    y-value are processed before points with a larger y-value; as a result, if
    the polygon is a square, the bottom-left vertex would be the start point,
    the top-right vertex would be the end point, and both other vertices would
    be treated normally. Split and merge points are similarly ordered.

    Since monotone partitioning is normally the first step in triangulation, it
    is does not significantly deviate from using a sorted binary search tree
    to maintain where split point should connect to. Triangularization, however,
    must deal with partition boundaries being added at the same time. The main
    problem is when two merge points should be connected as part of the
    partitioning process, as triangles should be formed with both the middle
    chain and the chain on the other side. To accommodate this, before a point
    is added to a chain, the chain could be "extended" to subsume the next
    chain, which simplifies the triangle forming process.
    """

    # build linked data structure with additional information
    wrapped_points = _preculculate_points_info(points)
    # define sweep line variables
    priority_queue = PriorityQueue() # FIXME ensure 'leave' vertices are processed before 'enter' vertices
    chains = Chains()
    triangles = []
    for point in wrapped_points:
        if point.point_type:
            priority_queue.push(
                point,
                priority=(point.point, point.index), # FIXME sort by point_type
            )
    # start the sweep line
    sort_key_fn = (lambda pair: pair[0].point)
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
        # process the point
        if point.point_type == PointType.ENTER:
            chains.create_chain(point)
        elif point.point_type == PointType.LEAVE:
            triangles.extend(chains.extend_chain(
                chains.get_chain_at(point.widder_point, ClockDir.WIDDER),
                point,
                ClockDir.DEASIL,
            ))
            # FIXME should be able to change extend_chain to not need the next line
            chains.delete_chain(chains.get_chain_at(point, ClockDir.WIDDER))
        elif point.point_type == PointType.SPLIT:
            deasil_chain, widder_chain = chains.get_encompassing_chains(point)
            assert deasil_chain or widder_chain
            if deasil_chain != widder_chain:
                # the point is closest to where two chains meet
                # extend the both chains with the point
                if deasil_chain:
                    triangles.extend(chains.extend_chain(deasil_chain, point, ClockDir.WIDDER))
                if widder_chain:
                    triangles.extend(chains.extend_chain(widder_chain, point, ClockDir.DEASIL))
            else:
                # the point is closest to a single chain
                # extend the chain and potentially add a new one
                chain = deasil_chain
                posx_point = chain.posx_point
                if chain.posx_point == chain.deasil_point:
                    deasil_point = chain.deasil_point
                    deasil_chain = chain.deasil_chain
                    triangles.extend(chains.extend_chain(chain, point, ClockDir.DEASIL))
                    if deasil_chain:
                        triangles.extend(chains.extend_chain(deasil_chain, point, ClockDir.WIDDER))
                    else:
                        # need to be careful not to trigger the asserts
                        new_chain = Chain(deasil_point)
                        new_chain.add_point(point, ClockDir.WIDDER)
                        chains.add_chain(new_chain)
                else:
                    widder_point = chain.widder_point
                    widder_chain = chain.widder_chain
                    triangles.extend(chains.extend_chain(chain, point, ClockDir.WIDDER))
                    if widder_chain:
                        triangles.extend(chains.extend_chain(widder_chain, point, ClockDir.DEASIL))
                    else:
                        # need to be careful not to trigger the asserts
                        new_chain = Chain(widder_point)
                        new_chain.add_point(point, ClockDir.DEASIL)
                        chains.add_chain(new_chain)
        elif point.point_type == PointType.MERGE:
            triangles.extend(chains.extend_chain(
                chains.get_chain_at(point.deasil_point, ClockDir.DEASIL),
                point,
                ClockDir.WIDDER,
            ))
            triangles.extend(chains.extend_chain(
                chains.get_chain_at(point.widder_point, ClockDir.WIDDER),
                point,
                ClockDir.DEASIL,
            ))
            deasil_chain = chains.get_chain_at(point, ClockDir.DEASIL)
            widder_chain = chains.get_chain_at(point, ClockDir.WIDDER)
            deasil_chain.widder_chain = widder_chain
            widder_chain.deasil_chain = deasil_chain
        else:
            if point.negx_point == point.deasil_point:
                chain = chains.get_chain_at(point.negx_point, ClockDir.DEASIL)
            else:
                chain = chains.get_chain_at(point.negx_point, ClockDir.WIDDER)
            if point.negx_point == point.deasil_point:
                triangles.extend(chains.extend_chain(
                    chain,
                    point,
                    ClockDir.WIDDER,
                ))
            else:
                triangles.extend(chains.extend_chain(
                    chain,
                    point,
                    ClockDir.DEASIL,
                ))
            priority_queue.push(
                point.posx_point,
                priority=(point.posx_point.point, point.posx_point.index), # FIXME sort by point_type
            )
        #chains.validate()
    return triangles
