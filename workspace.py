#!/home/justinnhli/.local/share/venv/animabotics/bin/python3

"""Utility algorithms."""

from collections import defaultdict, Counter, namedtuple
from collections.abc import Sequence
from enum import IntEnum, Enum
from math import inf as INF, pi as PI, copysign, nextafter
from statistics import mean
from typing import Any, Optional, Union

from animabotics import SortedDict, PriorityQueue
from animabotics import Point2D, Segment, ConvexPolygon
from animabotics import BasicWindow, Color


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

    def __repr__(self):
        # type: () -> str
        return self.name


class ClockDir(Enum):
    """Enum for clockwise directions."""
    DEASIL = -1
    WIDDER = 1

    def __repr__(self):
        # type: () -> str
        if self == ClockDir.DEASIL:
            return 'DEASIL'
        else:
            return 'WIDDER'

    @property
    def opposite(self):
        # type: () -> ClockDir
        """The opposite direction."""
        if self == ClockDir.DEASIL:
            return ClockDir.WIDDER
        else:
            return ClockDir.DEASIL


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
        self.negx_point = None # type: WrappedPoint
        self.posx_point = None # type: WrappedPoint
        self.negx_slope = 0.0
        self.posx_slope = 0.0

    def __repr__(self):
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
    def mean_slopes(self):
        # type: () -> tuple[float, float]
        """Calculate the mean slope in the neg-x and pos-x directions."""
        negx_slopes = []
        posx_slopes = []
        point_slopes = [
            (self.deasil_point.point, self.deasil_segment.slope),
            (self.widder_point.point, self.widder_segment.slope),
        ]
        for other_point, slope in point_slopes:
            if abs(slope) == float('inf'):
                continue
            if self.point < other_point:
                posx_slopes.append(slope)
            else:
                negx_slopes.append(-slope)
        return (
            (mean(negx_slopes) if negx_slopes else None),
            (mean(posx_slopes) if posx_slopes else None),
        )

    def get_dir_point(self, clock_dir):
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_point
        else:
            return self.widder_point

    def get_dir_segment(self, clock_dir):
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
        negx_mean_1, posx_mean_1 = point1.mean_slopes
        negx_mean_2, posx_mean_2 = point2.mean_slopes
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

    def __repr__(self):
        # type: () -> str
        return f'WrappedKey({self.point}, {self.point.point_type})'

    @property
    def key(self):
        # type: () -> tuple[float, float, PointType]
        """Return the comparison key."""
        return (self.point.x, self.point.y, self.point.point_type)


class Chain:
    """A chain of untriangulated points to the left of the sweep line.

    Chains represent points in widdershins order (as in the original polygon). 
    Chains are non-strictly monotonic; for all adjacent points p and q, either:

    * (p.x, p.y) > (q.x, q.y)
    * or p.x < q.x
    """

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

    def __repr__(self):
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
        return self.points[self.posx_index]

    def get_dir_point(self, clock_dir):
        # type: (ClockDir) -> WrappedPoint
        """Get the end point in either clock direction."""
        if clock_dir == ClockDir.DEASIL:
            return self.deasil_point
        else:
            return self.widder_point

    def get_dir_dir_point(self, clock_dir):
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
        # update the pos-x pointer
        '''
        # check the monotonicity invariant. This is necessary to ensure that
        # degenerate triangles (with area = 0) will not be created.
        if len(self.points) > 1:
            point1 = self.points[0]
            point2 = self.points[1]
            if point1.point > point2.point:
                for point1, point2 in zip(self.points[:-1], self.points[1:]):
                    if not point1.point > point2.point:
                        raise ValueError(' '.join((
                            'cannot triangulate;',
                            'perhaps the polygon is not simple or is disconnected?',
                        )))
            elif point1.point.x < point2.point.x:
                for point1, point2 in zip(self.points[:-1], self.points[1:]):
                    if not point1.point.x < point2.point.x:
                        raise ValueError(' '.join((
                            'cannot triangulate;',
                            'perhaps the polygon is not simple or is disconnected?',
                        )))
            else:
                assert False
        '''
        self.validate()
        return triangles

    def interval_at(self, x):
        # type: (float) -> tuple[float, float]
        """Get the upper and lower bounds of the chain at the given x-value."""
        # calculate the slope of the adjacent segments, if not boxed in by other chains
        if self.deasil_point.deasil_point.x == self.deasil_point.x:
            deasil_slope = float('inf')
            deasil_y = max(
                self.deasil_point.y,
                self.deasil_point.deasil_point.y,
            )
        else:
            deasil_slope = self.deasil_point.deasil_segment.slope
            deasil_y = self.deasil_point.y + deasil_slope * (x - self.deasil_point.x)
        if self.widder_point.widder_point.x == self.widder_point.x:
            widder_slope = float('inf')
            widder_y = min(
                self.widder_point.y,
                self.widder_point.widder_point.y,
            )
        else:
            widder_slope = self.widder_point.widder_segment.slope
            widder_y = self.widder_point.y + widder_slope * (x - self.widder_point.x)
        # if deasil_y < widder_y, the two lines intersect before x
        # give the y value of the intersect, being careful of the case where one of the slopes is 0
        if deasil_y < widder_y:
            if deasil_slope == 0:
                return deasil_y, deasil_y
            elif widder_slope == 0:
                return widder_y, widder_y
            else:
                intersect_y = self.deasil_point.deasil_segment.intersect(
                    self.widder_point.widder_segment,
                )
                return intersect_y, intersect_y
        else:
            return deasil_y, widder_y

    def validate(self): # pragma: no cover
        # type: () -> None
        """Validate the chain."""
        '''
        # check that the chain is monotonic
        if len(self.points) > 1:
            point1 = self.points[0]
            point2 = self.points[1]
            if point1.point > point2.point:
                for point1, point2 in zip(self.points[:-1], self.points[1:]):
                    assert point1.point > point2.point, self.points
            elif point1.point.x < point2.point.x:
                for point1, point2 in zip(self.points[:-1], self.points[1:]):
                    assert point1.point.x < point2.point.x
            else:
                assert False, self.points
        '''
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
            if other == self.chain.get_dir_point(self.clock_dir):
                assert False
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
            if other == self.chain.get_dir_point(self.clock_dir):
                assert False
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

    def __repr__(self):
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
        # FIXME still dislike the fact that two structures are needed here
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
        # FIXME it should be possible to do this without removing and re-adding the chain
        self.remove_chain(chain)
        self.triangles.extend(chain.add_point(point, clock_dir))
        # decide whether to reinsert the chain
        if not (len(chain) == 2 and chain.deasil_point.deasil_point == chain.widder_point):
            # if the chain is not the last one due to a LEAVE point
            # it is curving away and need to be reinserted
            self.add_chain(chain)
            chain.validate()

    def remove_chain(self, chain):
        del self.tree[chain.get_dir_key(ClockDir.DEASIL)]
        del self.tree[chain.get_dir_key(ClockDir.WIDDER)]

    def merge_chains_at(self, point):
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


def _preculculate_points_info(polygon_index, points):
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
            wrapped_point.negx_point = deasil_point
            wrapped_point.posx_point = widder_point
        else:
            wrapped_point.negx_point = widder_point
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

    # initialize sweep line variables
    priority_queue = PriorityQueue(key=WrappedPointPriority) # type: PriorityQueue[WrappedPointPriority, WrappedPoint]
    chains = Chains()
    for point in _preculculate_points_info(0, points):
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
        #print(point, point.point_type)
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
            if point.negx_point == point.deasil_point:
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
        chains.validate()
        #_print_chains(chains)
        #_visualize_state(points, chains)
    return tuple(chains.triangles)


POLYGON_PARTITION_DATASET = (
    # start, add, end
    (
        Point2D(4, 1), Point2D(2, 2), Point2D(-1, 2), Point2D(-3, 1),
        Point2D(-4, -1), Point2D(-2, -2), Point2D(1, -2), Point2D(3, -1),
    ),
    (
        Point2D(-8, 0), Point2D(-5, -1), Point2D(-3, -2),
        Point2D(-2, -3), Point2D(-1, -5), Point2D(0, -8),
        Point2D(1, 1),
    ),
    (
        Point2D(-8, 0), Point2D(-5, -1), Point2D(-3, -2),
        Point2D(-2, -3), Point2D(-1, -5), Point2D(0, -8),
        Point2D(1, -4), Point2D(3, 0),
    ),
    (
        Point2D(8, -4), Point2D(7, 4), Point2D(5, 4), Point2D(4, 1), Point2D(3, -1),
        Point2D(2, -2), Point2D(0, -3), Point2D(-1, 4), Point2D(-8, 4), Point2D(-8, 1),
        Point2D(-6, 2), Point2D(-5, 2), Point2D(-4, 1), Point2D(-3, -1), Point2D(-2, -4),
    ),
    (
        Point2D(-2, 2), Point2D(-2, -2), Point2D(2, -2), Point2D(2, 2),
    ),
    (
        Point2D(-2, 2), Point2D(-2, 0), Point2D(-2, -2), Point2D(0, -2),
        Point2D(2, -2), Point2D(2, 0), Point2D(2, 2), Point2D(0, 2),
    ),
    # merge or split
    (
        Point2D(-1, 1), Point2D(0, 0), Point2D(-1, -1),
        Point2D(2, -1), Point2D(1, 1),
    ),
    (
        Point2D(-1, 1), Point2D(0, 0), Point2D(-1, -1),
        Point2D(2, -1),
    ),
    (
        Point2D(-1, 5), Point2D(0, 4), Point2D(-1, 3), Point2D(1, 2), Point2D(-1, 1), Point2D(0, 0),
        Point2D(-1, -1), Point2D(1, -2), Point2D(-1, -3), Point2D(0, -4), Point2D(-1, -5), Point2D(8, 0),
    ),
    (
        Point2D(-1, 2), Point2D(0, 0), Point2D(-2, 1),
        Point2D(1, -2), Point2D(2, -1),
    ),
    (
        Point2D(-1, 2), Point2D(0, 0), Point2D(-2, 1),
        Point2D(2, -2), Point2D(1, 3),
    ),
    (
        Point2D(-1, 3), Point2D(-2, 2), Point2D(0, 0),
        Point2D(-2, 1), Point2D(1, -1),
    ),
    (
        Point2D(0, 3), Point2D(-1, 2), Point2D(0, 1),
        Point2D(0, -1), Point2D(-1, -2), Point2D(0, -3),
        Point2D(2, 0),
    ),
    (
        Point2D(1, 3), Point2D(-2, 2), Point2D(-1, 1), Point2D(0, 1),
        Point2D(0, -1), Point2D(-1, -2), Point2D(1, -3), Point2D(2, 0),
    ),
    (
        Point2D(3, 0), Point2D(2, 4), Point2D(-3, 4), Point2D(1, -1), Point2D(-1, 1),
        Point2D(-3, 1), Point2D(-2, 0), Point2D(-3, -1), Point2D(-3, -4), Point2D(2, -4),
    ),
    (
        Point2D(3, 0), Point2D(2, 4), Point2D(-3, 4), Point2D(1, -1), Point2D(-1, 1),
        Point2D(-3, 1), Point2D(-2, 0), Point2D(-6, -4), Point2D(2, -4),
    ),
    (
        Point2D(-2, 2),
        Point2D(0, -1),
        Point2D(-2, -2),
        Point2D(1, -2),
        Point2D(1, 1),
        Point2D(2, 2),
    ),
    (
        Point2D(-2, 2),
        Point2D(0, -1),
        Point2D(-2, -2),
        Point2D(0, -2),
        Point2D(1, 1),
        Point2D(2, 2),
    ),
    (
        Point2D(0, 0), Point2D(8, 2), Point2D(7, 4),
        Point2D(8, 6), Point2D(7, 5), Point2D(6, 3), Point2D(5, 2), Point2D(3, 1),
    ),
    # merge and split
    (
        Point2D(0, 2), Point2D(-2, 1), Point2D(-1, 0), Point2D(-2, -1),
        Point2D(0, -2), Point2D(2, -1), Point2D(1, 0), Point2D(2, 1),
    ),
    (
        Point2D(-2, 1), Point2D(-1, 0), Point2D(-2, -1),
        Point2D(2, -1), Point2D(1, 0), Point2D(2, 1),
    ),
    (
        Point2D(-2, 4), Point2D(0, 3), Point2D(-2, 2), Point2D(0, 1),
        Point2D(-2, -1), Point2D(0, -2), Point2D(-2, -3), Point2D(-1, -4),
        Point2D(2, -4), Point2D(0, -3), Point2D(2, -2), Point2D(0, -1),
        Point2D(2, 1), Point2D(0, 2), Point2D(2, 3), Point2D(1, 4),
    ),
    (
        Point2D(3, 0),
        Point2D(1, 2), Point2D(3, 4),
        Point2D(-2, 4), Point2D(-1, 3), Point2D(-2, 2), Point2D(-1, 1),
        Point2D(-2, 0),
        Point2D(-1, -1), Point2D(-2, -2), Point2D(-1, -3), Point2D(-2, -4),
        Point2D(3, -4), Point2D(1, -2),
    ),
    (
        Point2D(3, 0),
        Point2D(1, 2), Point2D(3, 4),
        Point2D(-4, 4), Point2D(-1, 3), Point2D(-2, 2), Point2D(-1, 1),
        Point2D(-2, 0),
        Point2D(-1, -1), Point2D(-2, -2), Point2D(-1, -3), Point2D(-4, -4),
        Point2D(3, -4), Point2D(1, -2),
    ),
    (
        Point2D(1, 0), Point2D(2, 5), Point2D(-4, 1), Point2D(-2, 2), Point2D(-1, 2),
        Point2D(0, 0), Point2D(-1, -2), Point2D(-2, -2), Point2D(-4, -1), Point2D(2, -5),
    ),
    (
        Point2D(1, 0), Point2D(2, 5), Point2D(-4, 1), Point2D(-2, 2), Point2D(-1, 2),
        Point2D(-1, -2), Point2D(-2, -2), Point2D(-4, -1), Point2D(2, -5),
    ),
    (
        Point2D(-2, 2),
        Point2D(-1, 1),
        Point2D(-2, -2),
        Point2D(2, -2),
        Point2D(0, -1),
        Point2D(2, 2),
    ),
    (
        Point2D(0, -5), Point2D(10, -3), Point2D(9, 0), Point2D(10, 3),
        Point2D(0, 5), Point2D(3, 4), Point2D(5, 3), Point2D(6, 2),
        Point2D(7, 0), Point2D(6, -2), Point2D(5, -3), Point2D(3, -4),
    ),
    (
        Point2D(-2, 4),
        Point2D(-2, -4),
        Point2D(0, -1),
        Point2D(2, -4),
        Point2D(2, -3),
        Point2D(-1, 2),
        Point2D(2, -2),
        Point2D(2, 4),
        Point2D(0, 1),
    ),
    # repeated points and opposite colinear segments
    (
        Point2D(0, 0), Point2D(1, 1), Point2D(2, 0), Point2D(1, -1),
        Point2D(0, 0), Point2D(2, -3), Point2D(4, 0), Point2D(2, 3),
    ),
    (
        Point2D(2, 0), Point2D(0, 2), Point2D(-2, 0), Point2D(0, -2), Point2D(2, 0),
        Point2D(1, 0), Point2D(0, -1), Point2D(-1, 0), Point2D(0, 1), Point2D(1, 0),
    ),
    (
        Point2D(2, 0), Point2D(0, 2), Point2D(-3, 1), Point2D(0, -2), Point2D(2, 0),
        Point2D(1, 0), Point2D(0, -1), Point2D(-1, 0), Point2D(0, 1), Point2D(1, 0),
    ),
    (
        Point2D(0, 0), Point2D(2, -3), Point2D(1, -1), Point2D(4, -3), Point2D(4, -1),
        Point2D(1, 0), Point2D(4, 1), Point2D(4, 3), Point2D(1, 1), Point2D(2, 3),
        Point2D(0, 0), Point2D(3, 2), Point2D(3, 1),
        Point2D(0, 0), Point2D(3, -1), Point2D(3, -2),
    ),
    (
        Point2D(0, -4), Point2D(4, -4), Point2D(4, 4), Point2D(-4, 4), Point2D(-4, -4), Point2D(0, -4), Point2D(0, 0),
        Point2D(-1, -2), Point2D(-2, -1), Point2D(0, 0),
        Point2D(-3, -1), Point2D(-3, 1), Point2D(0, 0),
        Point2D(-2, 1), Point2D(-1, 2), Point2D(0, 0),
        Point2D(-1, 3), Point2D(1, 3), Point2D(0, 0),
        Point2D(1, 2), Point2D(2, 1), Point2D(0, 0),
        Point2D(3, 1), Point2D(3, -1), Point2D(0, 0),
        Point2D(2, -1), Point2D(1, -2), Point2D(0, 0),
    ),
)


def _print_chains(chains):
    for chain_end, chain in chains.tree.items():
        print('   ', chain_end)
        print('       ', chain)


def _visualize_state(points, chains):
    window = BasicWindow(600, 400)
    if points:
        shifted = points[1:] + (points[0],)
        for point1, point2 in zip(points, shifted):
            window.add_geometry(Segment(point1, point2))
    for chain in chains.tree.values():
        for point1, point2 in zip(chain.points[1:], chain.points[:-1]):
            window.add_geometry(
                Segment(point1, point2),
                line_color=Color(0.1, 1, 1),
            )
    window.camera.zoom_level = 15
    window.start()


def _validate_partition(points, partition_indices):
    # type: (Sequence[Point2D], tuple[tuple[int, ...], ...]) -> None
    components = (
        ConvexPolygon(points=tuple(points[i] for i in index))
        for index in partition_indices
    )
    # initialize the segments with the _clockwise_ perimeter
    # which will be "canceled out" during the verification
    boundary_segments = set(
        Segment(points[i], points[i - 1])
        for i in range(len(points))
    )
    internal_segments = set() # type: set[Segment]
    # verify each component
    for component in components:
        # verify component goes does not go clockwise
        assert all(
            Segment.orientation(
                component.points[i - 1],
                component.points[i],
                component.points[i + 1],
            ) != 1
            for i in range(-2, len(component.points) - 2)
        )
        # verify component angles are convex
        assert all(
            Segment.angle(
                component.points[i - 1],
                component.points[i],
                component.points[i + 1],
            ) <= 2 * PI
            for i in range(-2, len(component.points) - 2)
        )
        # verify component has non-zero area
        assert component.area > 0
        # verify that all component edges either:
        # * have a twin that belongs to another component, or
        # * is part of the perimeter of the polygon
        for segment in component.segments:
            if segment.twin in boundary_segments:
                boundary_segments.remove(segment.twin)
            elif segment.twin in internal_segments:
                internal_segments.remove(segment.twin)
            else:
                assert segment not in internal_segments
                internal_segments.add(segment)
    assert not boundary_segments, boundary_segments
    assert not internal_segments, internal_segments


def test_polygon_triangulation_good(debug_index=None, debug_variant=None):
    # type: () -> None
    """Test successful polygon triangulations."""
    for index, points in enumerate(POLYGON_PARTITION_DATASET):
        if debug_index is not None and index != debug_index:
            continue
        variants = (
            ('', points),
            (
                'y',
                tuple(reversed([
                    Point2D.from_matrix(point.matrix.y_reflection) for point in points
                ])),
            ),
            (
                'x',
                tuple(reversed([
                    Point2D.from_matrix(point.matrix.x_reflection) for point in points
                ])),
            ),
            (
                'xy',
                tuple(
                    Point2D.from_matrix(point.matrix.x_reflection.y_reflection) for point in points
                ),
            ),
        )
        for marker, variant_points in variants:
            if debug_variant is not None and marker != debug_variant:
                continue
            print()
            print(f'POLYGON {index}{marker}')
            for i, point in enumerate(variant_points):
                print('   ', i, point)
            print()
            _validate_partition(variant_points, triangulate_polygon(variant_points))


def main():
    import sys
    import re
    args = sys.argv[1:]
    debug_index = None
    debug_variant = None
    if len(sys.argv) > 1:
        match = re.fullmatch('([0-9]+)([xy]*)', sys.argv[1])
        if not match:
            print(f'unrecognized arguments: {sys.argv}')
        debug_index = int(match.group(1))
        debug_variant = match.group(2)
    print(debug_index, debug_variant)
    test_polygon_triangulation_good(debug_index, debug_variant)


if __name__ == '__main__':
    main()
