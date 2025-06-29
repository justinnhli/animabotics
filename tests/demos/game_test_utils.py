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
        if class_name not in attributes:
            continue
        values = []
        for key in class_keys[class_name]:
            value = getattr(obj, key) 
            if hasattr(value, '__round__'):
                values.append(round(value, 6))
            else:
                values.append(value)
        obj_key = (class_name, tuple(values))
        if obj_key not in attr_counts or attr_counts[obj_key] <= 0:
            message = [f'unexpected {class_name} object with attributes:']
            for key in class_keys[class_name]:
                value = getattr(obj, key) 
                message.append(f'    {key}={value}')
            assert False, '\n'.join(message)
        attr_counts[obj_key] -= 1
        if attr_counts[obj_key] == 0:
            del attr_counts[obj_key]
    if attr_counts:
        message = ['failed to find objects:']
        for class_name, values in attr_counts.items():
            key = class_keys[class_name]
            message.append(f'    {class_name}')
            for value in values:
                message.append(f'        {key}={value}')
        assert False, '\n'.join(message)
