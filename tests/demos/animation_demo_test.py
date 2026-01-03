#!/usr/bin/env python3

from collections import defaultdict

from animabotics import Point2D
from demos.animation_demo import Bouncy


def assert_object_attributes(objects, attributes):
    # type: (Sequence[GameObject], dict[str, list[dict[str, Any]]]) -> None
    # organize the attributes so they can be easily matched with objects
    class_keys = {}
    attr_counts = defaultdict(int)
    for class_name, class_attributes in attributes.items():
        keys = set(class_attributes[0].keys())
        sorted_keys = sorted(keys)
        for obj_attributes in class_attributes:
            assert keys == set(obj_attributes.keys())
            values = tuple(obj_attributes[key] for key in sorted_keys)
            attr_counts[(class_name, values)] += 1
        class_keys[class_name] = sorted(keys)
    # organize the objects so they can be easily matched with attributes
    obj_counts = defaultdict(int)
    for obj in objects:
        class_name = type(obj).__name__
        assert class_name in attributes
        values = []
        for key in class_keys[class_name]:
            value = getattr(obj, key) 
            if hasattr(value, '__round__'):
                values.append(round(value, 6))
            else:
                values.append(value)
        obj_key = (class_name, tuple(values))
        assert obj_key in attr_counts and attr_counts[obj_key] > 0
        attr_counts[obj_key] -= 1
        if attr_counts[obj_key] == 0:
            del attr_counts[obj_key]
    assert not attr_counts


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


def test_animation():
    bouncy = Bouncy()
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


if __name__ == '__main__':
    main()
