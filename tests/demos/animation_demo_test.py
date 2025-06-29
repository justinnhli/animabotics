"""Tests for Animation Demo."""

from animabotics import Point2D
from demos.animation_demo import AnimationDemo

from game_test_utils import assert_object_attributes


def assert_ball_size(objects, len_x, len_y):
    for obj in objects:
        if type(obj).__name__ != 'AnimatedBall':
            continue
        polygon = obj.sprite.shapes[0].polygon
        max_x = max(point.x for point in polygon.points)
        min_x = min(point.x for point in polygon.points)
        max_y = max(point.y for point in polygon.points)
        min_y = min(point.y for point in polygon.points)
        assert max_x - min_x == len_x
        assert max_y - min_y == len_y
        return


def test_animation_demo():
    bouncy = AnimationDemo()
    bouncy.prestart()
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 825)}],
            'AnimatedBall': [{'position': Point2D(200, 825)}],
        },
    )
    assert_ball_size(bouncy.objects, 100, 100)
    bouncy.run_for_msec(200)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 805)}],
            'AnimatedBall': [{'position': Point2D(200, 805)}],
        },
    )
    bouncy.run_for_msec(800)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 325)}],
            'AnimatedBall': [{'position': Point2D(200, 325)}],
        },
    )
    bouncy.run_for_msec(280)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 5.8)}],
            'AnimatedBall': [{'position': Point2D(200, 5.8)}],
        },
    )
    bouncy.run_for_msec(40)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 0)}],
            'AnimatedBall': [{'position': Point2D(200, 0)}],
        },
    )
    assert_ball_size(bouncy.objects, 120, 60)
    bouncy.run_for_msec(1200)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 810)}],
            'AnimatedBall': [{'position': Point2D(200, 810)}],
        },
    )
    bouncy.run_for_msec(200)
    assert_object_attributes(
        bouncy.objects, 
        {
            'Ground': [{'position': Point2D(0, -65)}],
            'StoicBall': [{'position': Point2D(-200, 805)}],
            'AnimatedBall': [{'position': Point2D(200, 805)}],
        },
    )
    assert_ball_size(bouncy.objects, 100, 100)
