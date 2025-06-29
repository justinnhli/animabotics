"""Tests for Collision Demo."""

from collections import defaultdict

from animabotics import Point2D
from demos.collision_demo import CollisionDemo

from game_test_utils import assert_object_attributes


def test_collision_demo():
    demo = CollisionDemo(1, random_seed=8675309)
    # check the initial position of the ball
    demo.prestart()
    # check the position of the ball every second
    positions = [
        Point2D(-50, -46),
        Point2D(-20, 4),
        Point2D(10, 54),
        Point2D(40, 104),
        Point2D(70, 154),
        Point2D(100, 140),
        Point2D(130, 90),
        Point2D(160, 40),
        Point2D(190, -10),
        Point2D(220, -60),
        Point2D(250, -110),
        Point2D(265.6, -160),
        Point2D(235.6, -138),
        Point2D(205.6, -88),
        Point2D(175.6, -38),
        Point2D(145.6, 12),
        Point2D(115.6, 62),
        Point2D(85.6, 112),
        Point2D(55.6, 162),
        Point2D(25.6, 132),
        Point2D(-4.4, 82),
    ]
    for position in positions:
        assert_object_attributes(
            demo.objects,
            {
                'Ball': [{'position': position}],
            },
        )
        demo.run_for_msec(1000)
    assert_object_attributes(
        demo.objects,
        {
            'Ball': [{'position': Point2D(-34.4, 32)}],
        },
    )
