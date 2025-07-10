"""Utility algorithms."""

from collections import defaultdict, Counter
from collections.abc import Callable, Sequence
from enum import IntEnum
from math import inf as INF, copysign, nextafter
from typing import Any, Optional, Union

from .data_structures import SortedDict, PriorityQueue
from .simplex import Point2D, Segment, Triangle


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


class Dir(IntEnum):
    """Enum for different directions."""
    PREV = -1
    NEXT = 1

    @property
    def opposite(self):
        # type: () -> Dir
        """The opposite direction."""
        return Dir(-1 * self)


class Chain:
    """A chain of untriangulated points."""

    def __init__(self, point):
        # type: (Point2D) -> None
        self.points = []
        self.points = [point]

    def __eq__(self, other):
        # type: (Any) -> bool
        return self.points == other.points

    def __len__(self):
        # type: () -> int
        return len(self.points)

    def __getitem__(self, index):
        # type: (slice) -> list[Point2D]
        return self.points[index]

    def __repr__(self):
        # type: () -> str
        return f'Chain({self.points})'

    def prev(self, index=1):
        # type: (int) -> Point2D
        """The nth point in the previous direction."""
        return self.points[index - 1]

    def next(self, index=1):
        # type: (int) -> Point2D
        """The nth point in the next direction."""
        return self.points[-index]

    def prev_pair(self):
        # type: () -> tuple[Point2D, Point2D]
        """The first two points in the previous direction."""
        return (self.points[0], self.points[1])

    def next_pair(self):
        # type: () -> tuple[Point2D, Point2D]
        """The first two points in the next direction."""
        return (self.points[-2], self.points[-1])

    def add_prev(self, point):
        # type: (Point2D) -> None
        """Add a point in the previous direction."""
        self.points.insert(0, point)

    def add_next(self, point):
        # type: (Point2D) -> None
        """Add a point in the next direction."""
        self.points.append(point)

    def trim_prev(self):
        # type: () -> Point2D
        """Remove a point in the previous direction."""
        result = self.points[0]
        self.points = self.points[1:]
        return result

    def trim_next(self):
        # type: () -> Point2D
        """Remove a point in the next direction."""
        result = self.points[-1]
        self.points = self.points[:-1]
        return result


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

    class MonotoneSegmentWrapper(_SegmentWrapper):
        """A wrapper class for ordering Segments."""

        @property
        def key(self):
            # type: () -> tuple[float, float, float]
            """Return the comparison key.

            Since segments never intersect in the middle, this key sorts
            segments by the vertical order on either side.
            """
            return (self.y, self.segment.point1.y, self.segment.slope)

    # initialize the three main data structures
    priority_queue = PriorityQueue() # type: PriorityQueue[tuple[float, float], Point2D]
    open_chains = {} # type: dict[tuple[Point2D, Dir], Chain]
    partitions = SortedDict() # type: SortedDict[Union[MonotoneSegmentWrapper, float], Point2D]
    # cache information about the points, and enqueue points whose neighbors are to the right
    # we do this to deal with vertical segments, by tracking which point is further "left"
    point_info = {}
    for i in range(-1, len(points) - 1):
        point = points[i]
        prev_point = points[i - 1]
        next_point = points[i + 1]
        orientation = Segment.orientation(prev_point, point, next_point)
        point_type = None
        if prev_point > point and next_point > point:
            if orientation == -1:
                point_type = 'start'
            elif orientation == 1:
                point_type = 'split'
            else:
                assert False, point
        elif prev_point < point and next_point < point:
            if orientation == -1:
                point_type = 'end'
            elif orientation == 1:
                point_type = 'merge'
            else:
                assert False, point
        else:
            point_type = 'add'
        assert point_type
        point_info[point] = (
            (prev_point, next_point),
            (
                MonotoneSegmentWrapper(
                    Segment(prev_point, point)
                    if prev_point < point else
                    Segment(point, prev_point)
                ),
                MonotoneSegmentWrapper(
                    Segment(next_point, point)
                    if next_point < point else
                    Segment(point, next_point)
                ),
            ),
            point_type,
        )
        if point_type in ('start', 'split'):
            priority_queue.push(point)
    # initialize results
    processed = set()
    results = [] # type: list[Triangle]

    def add_to_chain(chain, point, direction):
        # type: (Chain, Point2D, Dir) -> None
        # pylint: disable = superfluous-parens, unnecessary-lambda-assignment
        # direction is the from the point to the chain
        # define everything in terms of head (towards the point) and tail (away from the point)
        if direction == Dir.PREV:
            head_fn = (lambda chain: chain.next()) # type: Callable[[Chain], Point2D]
            tail_fn = (lambda chain: chain.prev()) # type: Callable[[Chain], Point2D]
            pair_fn = (lambda chain: chain.next_pair()) # type: Callable[[Chain], tuple[Point2D, Point2D]]
            trim_head_fn = (lambda chain: chain.trim_next()) # type: Callable[[Chain], Point2D]
            add_head_fn = chain.add_next
            add_tail_fn = chain.add_prev
        elif direction == Dir.NEXT:
            head_fn = (lambda chain: chain.prev())
            tail_fn = (lambda chain: chain.next())
            pair_fn = (lambda chain: chain.prev_pair())
            trim_head_fn = (lambda chain: chain.trim_prev())
            add_head_fn = chain.add_prev
            add_tail_fn = chain.add_next
        else:
            assert False
        # delete the head before it changes
        del open_chains[(head_fn(chain), direction)]
        # extend the chain if necessary
        if len(chain) > 1 and (tail_fn(chain), direction) in open_chains:
            other_chain = open_chains[(tail_fn(chain), direction)]
            should_extend = (
                len(other_chain) > 1
                and point_info[head_fn(other_chain)][2] != 'split'
            )
            if should_extend:
                del open_chains[(tail_fn(chain), direction.opposite)]
                del open_chains[(head_fn(other_chain), direction)]
                open_chains[(tail_fn(other_chain), direction.opposite)] = chain
                trim_head_fn(other_chain)
                while other_chain:
                    add_tail_fn(trim_head_fn(other_chain))
        # form all triangles possible
        while len(chain) > 1:
            if Segment.orientation(*pair_fn(chain), point) != -1:
                break
            results.append(Triangle(*pair_fn(chain), point))
            trim_head_fn(chain)
        # update the chain
        add_head_fn(point)
        open_chains[(head_fn(chain), direction)] = chain

    def end_chain(chain, point):
        # type: (Chain, Point2D) -> None
        for point1, point2 in zip(chain[:-1], chain[1:]):
            results.append(Triangle(point, point1, point2))

    # start the sweep
    while priority_queue:
        _, point = priority_queue.pop()
        processed.add(point)
        MonotoneSegmentWrapper.sweep_x = point.x
        (
            (prev_point, next_point),
            (prev_segment, next_segment),
            point_type,
        ) = point_info[point]
        if point_type == 'start':
            # start a new chain
            chain = Chain(point)
            open_chains[(point, Dir.PREV)] = chain
            open_chains[(point, Dir.NEXT)] = chain
            partitions[prev_segment] = point
            partitions[next_segment] = point
        elif point_type == 'add':
            # add a point to an existing chain
            # find the chain that is connected to this point and add to it
            if (prev_point, Dir.PREV) in open_chains:
                chain = open_chains[(prev_point, Dir.PREV)]
                direction = Dir.PREV
                del partitions[prev_segment]
                cursor_top = partitions.bracket(point.y)[1]
                partitions[next_segment] = point
                cursor_top.value = point
            elif (next_point, Dir.NEXT) in open_chains:
                chain = open_chains[(next_point, Dir.NEXT)]
                direction = Dir.NEXT
                del partitions[next_segment]
                cursor_bot = partitions.bracket(point.y)[0]
                partitions[prev_segment] = point
                cursor_bot.value = point
            else:
                assert False
            add_to_chain(chain, point, direction)
        elif point_type == 'end':
            # end a chain
            # form all triangles
            link_point = next_point
            while link_point != prev_point:
                chain = open_chains[(link_point, Dir.NEXT)]
                end_chain(chain, point)
                del open_chains[(chain.prev(), Dir.NEXT)]
                del open_chains[(chain.next(), Dir.PREV)]
                link_point = chain.next()
            del partitions[prev_segment]
            del partitions[next_segment]
        elif point_type == 'merge':
            # merge two chains
            add_to_chain(open_chains[(prev_point, Dir.PREV)], point, Dir.PREV)
            add_to_chain(open_chains[(next_point, Dir.NEXT)], point, Dir.NEXT)
            # update partitions
            del partitions[prev_segment]
            del partitions[next_segment]
            cursor_prev, cursor_next = partitions.bracket(point.y)
            cursor_prev.value = point
            cursor_next.value = point
        elif point_type == 'split':
            # split a chain
            # retrieve the stored point for this position
            cursor_bot, cursor_top = partitions.bracket(point.y)
            assert cursor_bot and cursor_top
            prev_chain = open_chains.get((cursor_bot.value, Dir.PREV))
            next_chain = open_chains.get((cursor_top.value, Dir.NEXT))
            assert prev_chain or next_chain
            # determine if only one or both chains should be closed
            # * if there is only one chain, deal with that
            # * if one of the chains is colinear, ignore it
            if prev_chain and next_chain and prev_chain == next_chain:
                # the diagonal points are the ends of a chain
                # form all triangles
                end_chain(prev_chain, point)
                # store chain information
                chain_prev = prev_chain.prev()
                chain_next = prev_chain.next()
                # clean up old chains
                del open_chains[(prev_chain.prev(), Dir.NEXT)]
                del open_chains[(prev_chain.next(), Dir.PREV)]
                prev_chain = None
                next_chain = None
            else:
                # the diagonal point is a merge point
                # cache the end of a chain
                other_end = None
                if prev_chain:
                    other_end = prev_chain.next()
                elif next_chain:
                    other_end = next_chain.prev()
                else:
                    assert False
                # form all triangles
                if not prev_chain:
                    chain_prev = other_end
                    prev_chain = None
                else:
                    # otherwise, add the point to the chain
                    add_to_chain(prev_chain, point, Dir.PREV)
                    # store chain information
                    chain_prev = prev_chain.prev()
                    # clean up old chains
                    del open_chains[(prev_chain.prev(), Dir.NEXT)]
                    del open_chains[(prev_chain.next(), Dir.PREV)]
                if not next_chain:
                    chain_next = other_end
                    next_chain = None
                else:
                    # otherwise, add the point to the chain
                    add_to_chain(next_chain, point, Dir.NEXT)
                    # store chain information
                    chain_next = next_chain.next()
                    # clean up old chains
                    del open_chains[(next_chain.prev(), Dir.NEXT)]
                    del open_chains[(next_chain.next(), Dir.PREV)]
            # add diagonal for top polygon
            if not prev_chain:
                prev_chain = Chain(chain_prev)
                prev_chain.add_next(point)
            open_chains[(prev_chain.prev(), Dir.NEXT)] = prev_chain
            open_chains[(prev_chain.next(), Dir.PREV)] = prev_chain
            partitions[MonotoneSegmentWrapper(Segment(point, next_point))] = point
            # add diagonal for bottom polygon
            if not next_chain:
                next_chain = Chain(chain_next)
                next_chain.add_prev(point)
            open_chains[(next_chain.prev(), Dir.NEXT)] = next_chain
            open_chains[(next_chain.next(), Dir.PREV)] = next_chain
            partitions[MonotoneSegmentWrapper(Segment(point, prev_point))] = point
        else:
            assert False
        # add the eligible neighbors to the priority queue, which are points:
        # 1. that have not already been processed
        # 2. all of whose "smaller" neighbors have been processed
        for neighbor in (prev_point, next_point):
            should_enqueue = (
                neighbor not in processed
                and all(
                    other > neighbor or other in processed
                    for other in point_info[neighbor][0]
                )
            )
            if should_enqueue:
                priority_queue.push(neighbor)
        counter = Counter((chain.prev(), chain.next()) for chain in open_chains.values())
        assert all(count == 2 for _, count in counter.most_common()), counter.most_common()
    assert len(open_chains) == len(partitions) == 0
    # convert the points to indices
    points_map = {point: index for index, point in enumerate(points)}
    return tuple(
        (
            points_map[triangle.point1],
            points_map[triangle.point2],
            points_map[triangle.point3],
        )
        for triangle in results
    )
