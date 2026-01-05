"""Utilities for checking game objects."""

from collections import defaultdict
from typing import Sequence

from animabotics import GameObject


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
